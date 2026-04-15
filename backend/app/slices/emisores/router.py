import base64
import logging
import os

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.core.dependencies import get_current_tenant
from .facturama_client import FacturamaClient
from .schema import CSDUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emisores", tags=["Emisores"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _load_encryptor() -> Fernet:
    """Carga la clave Fernet desde env al arrancar. Falla en startup si no esta configurada."""
    key = os.getenv("CSD_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError(
            "CSD_ENCRYPTION_KEY no configurada. "
            "Genera una con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


# Instancia unica cargada al importar el modulo (falla rapido si falta la clave)
_encryptor = _load_encryptor()


@router.post("/csd", response_model=CSDUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_csd(
    request: Request,
    rfc: str = Form(..., min_length=12, max_length=13, description="RFC del contribuyente"),
    cer_file: UploadFile = File(..., description="Archivo .cer"),
    key_file: UploadFile = File(..., description="Archivo .key"),
    password: str = Form(..., description="Contrasena del CSD"),
    tenant: dict = Depends(get_current_tenant)
):
    """
    Endpoint de carga asíncrona CSD multi-tenant.
    Cifra el .cer, .key y password en reposo (DB) antes de sincronizar con Facturama.
    """
    if not cer_file.filename.endswith(".cer") or not key_file.filename.endswith(".key"):
        raise HTTPException(status_code=422, detail="Extensiones de archivos inválidas. Requiere .cer y .key")

    try:
        cer_bytes = await cer_file.read()
        key_bytes = await key_file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Error leyendo los archivos enviados.")

    if len(cer_bytes) > MAX_FILE_SIZE or len(key_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande. Máximo 5 MB por archivo.")

    cer_b64 = base64.b64encode(cer_bytes).decode('utf-8')
    key_b64 = base64.b64encode(key_bytes).decode('utf-8')

    # Cifrado en reposo con clave Fernet estable
    encrypted_cer = _encryptor.encrypt(cer_bytes).decode()
    encrypted_key = _encryptor.encrypt(key_bytes).decode()
    encrypted_password = _encryptor.encrypt(password.encode()).decode()

    # Persistir en DB antes de llamar a Facturama (fuente de verdad local)
    db_pool = request.app.state.db_pool
    try:
        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO emisores (organization_id, rfc, cer_encrypted, key_encrypted, password_encrypted)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (organization_id, rfc) DO UPDATE
                        SET cer_encrypted = EXCLUDED.cer_encrypted,
                            key_encrypted = EXCLUDED.key_encrypted,
                            password_encrypted = EXCLUDED.password_encrypted,
                            facturama_synced = FALSE;
                    """,
                    (tenant["tenant_id"], rfc.upper(), encrypted_cer, encrypted_key, encrypted_password)
                )
                await conn.commit()
    except Exception:
        logger.exception("Error al persistir CSD en base de datos")
        raise HTTPException(status_code=500, detail="Error al guardar el CSD en la base de datos.")

    # Sincronizar con Facturama
    client = FacturamaClient()
    try:
        await client.upload_csd(rfc, cer_b64, key_b64, password)
        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE emisores SET facturama_synced = TRUE WHERE organization_id = %s AND rfc = %s",
                    (tenant["tenant_id"], rfc.upper())
                )
                await conn.commit()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error al sincronizar CSD con Facturama")
        raise HTTPException(
            status_code=502,
            detail="CSD guardado localmente pero falló la sincronización con Facturama."
        )

    return CSDUploadResponse(
        message="CSD validado y guardado cifrado.",
        rfc=rfc
    )
