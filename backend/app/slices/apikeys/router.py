import logging
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from psycopg.rows import dict_row

from app.core.dependencies import get_current_tenant
from .schema import ApiKeyCreateRequest, ApiKeyCreateResponse
from .security import hash_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/apikeys", tags=["API Keys B2B"])


@router.post("/generate", response_model=ApiKeyCreateResponse)
async def generate_api_key(
    payload: ApiKeyCreateRequest,
    request: Request,
    tenant: dict = Depends(get_current_tenant)
):
    """
    Genera una API Key productiva para un tenant B2B.
    Muestra la clave limpia UNA sola vez; persiste solo el hash bcrypt en PostgreSQL.
    """
    org_id = tenant["tenant_id"]

    raw_api_key = f"vanta_live_{secrets.token_urlsafe(48)}"
    hashed_key = hash_api_key(raw_api_key)
    prefix = raw_api_key[:15]
    key_id = str(uuid.uuid4())

    db_pool = request.app.state.db_pool
    try:
        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO api_keys (id, organization_id, nombre, prefix, hashed_key)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (key_id, org_id, payload.name, prefix, hashed_key)
                )
                await conn.commit()
    except Exception:
        logger.exception("Error al persistir API Key en base de datos")
        raise HTTPException(status_code=500, detail="Error al generar la API Key.")

    return ApiKeyCreateResponse(
        id=key_id,
        name=payload.name,
        api_key_plain=raw_api_key
    )


@router.get("/")
async def list_keys(request: Request, tenant: dict = Depends(get_current_tenant)):
    """Lista metadatos de las API Keys (prefijos y estados). NUNCA devuelve el hash."""
    org_id = tenant["tenant_id"]
    db_pool = request.app.state.db_pool

    async with db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, nombre, prefix, created_at, activa
                FROM api_keys
                WHERE organization_id = %s
                ORDER BY created_at DESC
                """,
                (org_id,)
            )
            keys = await cur.fetchall()

    return {"data": [dict(k) for k in keys]}


@router.delete("/{key_id}")
async def delete_key(
    key_id: str,
    request: Request,
    tenant: dict = Depends(get_current_tenant)
):
    """Revoca una API Key del tenant. Aislamiento garantizado por JWT (no puede borrar keys ajenas)."""
    org_id = tenant["tenant_id"]
    db_pool = request.app.state.db_pool

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE api_keys SET activa = FALSE
                WHERE id = %s AND organization_id = %s AND activa = TRUE
                """,
                (key_id, org_id)
            )
            affected = cur.rowcount
            await conn.commit()

    if affected == 0:
        return {"message": "La llave no existe en el contexto de esta organizacion."}

    return {"message": "API Key revocada exitosamente."}
