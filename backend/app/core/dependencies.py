"""
Dependencias Centralizadas — Vanta Facturacion
===============================================
`get_current_tenant` es la unica fuente de verdad para autorizacion.

Diseño de seguridad:
- Valida el JWT directamente desde el header `Authorization: Bearer <token>`.
- NO depende del middleware para obtener el tenant — es completamente auto-suficiente.
- Al usar `HTTPBearer`, FastAPI registra el esquema Bearer en el spec OpenAPI:
  Swagger UI muestra el candado en cada ruta protegida y el boton "Authorize" global.
- Previene IDOR: el `tenant_id` proviene del JWT firmado, nunca de headers del cliente.
"""

import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Al declarar este scheme, FastAPI lo registra en el OpenAPI spec automaticamente.
# Swagger UI mostrara el candado en todas las rutas que usen get_current_tenant.
bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Token JWT obtenido en `/api/v1/auth/login` o `/api/v1/auth/signup`.",
    auto_error=True,  # Devuelve 403 automaticamente si no se envia el header
)


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Dependency de FastAPI para autorizacion multitenant.

    Decodifica y valida el JWT directamente desde el header Authorization.
    No requiere middleware previo — cada ruta protegida es independiente.

    Returns:
        dict con:
            - tenant_id (str): ID unico del cliente en tabla `clientes`.
            - tenant_org (str): RFC del tenant (organizacion).

    Raises:
        HTTP 403 si no se envia el header Authorization (auto_error de HTTPBearer).
        HTTP 401 si el token esta expirado, es invalido, o le faltan claims.
        HTTP 500 si SECRET_KEY no esta configurada en el servidor.
    """
    secret = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuracion de servidor incompleta: SECRET_KEY ausente.",
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT expirado. Inicia sesion nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalido o corrupto.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_id = payload.get("id")
    tenant_org = payload.get("org")

    if not tenant_id or not tenant_org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT con claims incompletos (id u org ausentes).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"tenant_id": tenant_id, "tenant_org": tenant_org}
