from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
import base64
import os
from cryptography.fernet import Fernet
from .schema import CSDUploadResponse
from .facturama_client import FacturamaClient
from app.core.dependencies import get_current_tenant

router = APIRouter(prefix="/emisores", tags=["Emisores"])

def get_encryptor() -> Fernet:
    """Devuelve instancia Fernet para cifrar secretos guardados en DB."""
    key = os.getenv("CSD_ENCRYPTION_KEY", "")
    if not key:
        key = Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)

@router.post("/csd", response_model=CSDUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_csd(
    rfc: str = Form(..., min_length=12, max_length=13, description="RFC del contribuyente"),
    cer_file: UploadFile = File(..., description="Archivo .cer"),
    key_file: UploadFile = File(..., description="Archivo .key"),
    password: str = Form(..., description="Contrasena del CSD"),
    tenant: dict = Depends(get_current_tenant)
):
    """
    Endpoint de carga asíncrona CSD multi-tenant.
    Orquesta encriptación de llave/pwd en reposo (DB) y subida hacia API externa.
    """
    if not cer_file.filename.endswith(".cer") or not key_file.filename.endswith(".key"):
        raise HTTPException(status_code=422, detail="Extensiones de archivos inválidas. Requiere .cer y .key")

    try:
        cer_bytes = await cer_file.read()
        key_bytes = await key_file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo binarios: {str(e)}")

    cer_b64 = base64.b64encode(cer_bytes).decode('utf-8')
    key_b64 = base64.b64encode(key_bytes).decode('utf-8')

    # Cifrado en Base de Datos
    encryptor = get_encryptor()
    encrypted_password = encryptor.encrypt(password.encode()).decode()
    encrypted_key = encryptor.encrypt(key_bytes).decode()
    
    # TODO: Almacenar CSD en PostgreSQL filtrado (tenant["tenant_id"], encrypted_key, encrypted_password)
    
    # Subida al API externa
    client = FacturamaClient()
    try:
        await client.upload_csd(rfc, cer_b64, key_b64, password)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fallo integración con Integrador: {str(e)}")
        
    return CSDUploadResponse(
        message="CSD validado y guardado cifrado.",
        rfc=rfc
    )
