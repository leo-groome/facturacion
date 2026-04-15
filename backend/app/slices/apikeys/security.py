from fastapi import Header, HTTPException, status, Request
import bcrypt
import time
from typing import Dict, Tuple
from psycopg.rows import dict_row

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
    request: Request,
    x_api_key: str = Header(..., description="API Key externa proporcionada por integrador B2B"),
) -> str:
    """
    Autenticador para peticiones REST B2B.
    Valida la API Key contra el hash bcrypt en PostgreSQL y retorna el organization_id.
    """
    db_pool = request.app.state.db_pool

    # Buscar candidatos por prefijo (evita comparar bcrypt contra toda la tabla)
    prefix = x_api_key[:15]
    async with db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT organization_id, hashed_key FROM api_keys WHERE prefix = %s AND activa = TRUE",
                (prefix,)
            )
            candidates = await cur.fetchall()

    for row in candidates:
        if verify_api_key(x_api_key, row["hashed_key"]):
            return str(row["organization_id"])

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API Key inválida o revocada."
    )
