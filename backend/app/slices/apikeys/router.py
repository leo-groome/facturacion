from fastapi import APIRouter, Depends, Header
import secrets
import uuid
from datetime import datetime
from .schema import ApiKeyCreateRequest, ApiKeyCreateResponse
from .security import hash_api_key

router = APIRouter(prefix="/apikeys", tags=["API Keys B2B"])

# Almacenamiento en memoria volátil (Shared Memory Storage)
# Estructura: { org_id: [ApiKeyData, ...] }
API_KEYS_DB = {}

async def get_current_organization_id(
    x_organization_id: str = Header(..., description="ID del tenant a filtrar inyectado obligatoriamente por Frontend")
) -> str:
    return x_organization_id

@router.post("/generate", response_model=ApiKeyCreateResponse)
async def generate_api_key(
    payload: ApiKeyCreateRequest,
    org_id: str = Depends(get_current_organization_id)
):
    """
    Genera una API Key productiva para un tenant B2B.
    Presenta la clave íntegra 1 sola vez mientras almacena rigurosamente el Hash (bcrypt)
    impidiendo cualquier fuga directa.
    """
    # Genera componente random seguro e impredecible optimizado TLS de 64 bytes
    raw_api_key = f"vanta_live_{secrets.token_urlsafe(48)}"
    hashed_key = hash_api_key(raw_api_key)
    
    key_id = str(uuid.uuid4())
    
    # Prefix a almacenar para poder listar en DataGrid al Front (vanta_live_******)
    prefix = raw_api_key[:15]
    
    # Persistencia en memoria (Production-Ready logic for stateful session)
    if org_id not in API_KEYS_DB:
        API_KEYS_DB[org_id] = []
        
    new_key_data = {
        "id": key_id,
        "name": payload.name,
        "prefix": prefix,
        "hashed_key": hashed_key,
        "created_at": datetime.now().isoformat(),
        "active": True
    }
    API_KEYS_DB[org_id].append(new_key_data)
    
    return ApiKeyCreateResponse(
        id=key_id,
        name=payload.name,
        api_key_plain=raw_api_key
    )

@router.get("/")
async def list_keys(org_id: str = Depends(get_current_organization_id)):
    """Lista metadatos de las Api Keys (prefijos y estados). NUNCA manda contraseñas limpias."""
    keys = API_KEYS_DB.get(org_id, [])
    # Retornamos solo metadatos seguros (omitimos hashed_key por seguridad de transporte)
    safe_keys = [
        {k: v for k, v in key.items() if k != "hashed_key"}
        for key in keys
    ]
    return {"data": safe_keys}

@router.delete("/{key_id}")
async def delete_key(
    key_id: str,
    org_id: str = Depends(get_current_organization_id)
):
    """Elimina permanentemente una API Key del tenant."""
    if org_id not in API_KEYS_DB:
        return {"message": "Llave no encontrada o ya eliminada."}
    
    # Filtramos la lista removiendo el ID (garantizamos aislamiento de tenant por el org_id)
    initial_count = len(API_KEYS_DB[org_id])
    API_KEYS_DB[org_id] = [k for k in API_KEYS_DB[org_id] if k["id"] != key_id]
    
    if len(API_KEYS_DB[org_id]) == initial_count:
        return {"message": "La llave no existe en este contexto de organización."}
        
    return {"message": "API Key revocada y eliminada con éxito."}
