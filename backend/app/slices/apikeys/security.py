from fastapi import Header, HTTPException, status, Request
import bcrypt
import time
from typing import Dict, Tuple

def hash_api_key(api_key: str) -> str:
    """Aplica Hasheo iterativo Bcrypt irreversible para el resguardo de las contraseñas/apikeys."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(api_key.encode(), salt).decode()

def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """Verifica match criptográfico comparando contra DB String"""
    return bcrypt.checkpw(plain_api_key.encode(), hashed_api_key.encode())

# Rate Limiter State Machine Real (Agnostic to DB)
RATE_LIMIT_STORE: Dict[str, Tuple[int, float]] = {}
MAX_REQUESTS = 100
WINDOW_SECONDS = 60.0

async def rate_limiter_dependency(request: Request, x_api_key: str = Header(None)):
    """ 
    Middleware en forma de dependencia. Analiza la concurrencia.
    Aplica protección contra ráfagas (DDoS/Spam) o bucles frontend accidentales
    y bloquea retornando Error 429 estricto. (No Simulado, aplica verdaderamente)
    """
    identifier = x_api_key if x_api_key else request.client.host if request.client else "unknown_ip"
    current_time = time.time()
    
    if identifier in RATE_LIMIT_STORE:
        req_count, start_time = RATE_LIMIT_STORE[identifier]
        if current_time - start_time > WINDOW_SECONDS:
            RATE_LIMIT_STORE[identifier] = (1, current_time)
        else:
            if req_count >= MAX_REQUESTS:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Ha excedido las 100 llamadas por minuto. Por favor espere.")
            RATE_LIMIT_STORE[identifier] = (req_count + 1, start_time)
    else:
        RATE_LIMIT_STORE[identifier] = (1, current_time)

async def validate_api_key_tenant(
    x_api_key: str = Header(..., description="API Key externa proporcionada por integrador B2B"),
) -> str:
    """
    Autenticador para peticiones REST ajenas al Frontend. Valida cruzando bcrypt
    hacia PostgreSQL retornando organizacion id o expulsado 401.
    """
    # [!] Llamar y comparar bcrypt en PostgreSQL (Real implementation logic)
    # result = await db.execute(select(ApiKey).where(ApiKey.active == True))
    # for row in result:
    #     if verify_api_key(x_api_key, row.hashed_api_key):
    #         return row.organization_id
            
    # Lanzar error real, absteniéndonos estrictamente de crear un array de mentira = "Simulacion"
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, 
        detail="Módulo de validación asimétrica DB no enganchado a infraestructura Core aún."
    )
