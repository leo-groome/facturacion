"""
Modulo de Gestion de Base de Datos - Vanta Facturacion
=======================================================
Administra el ciclo de vida del pool asincrono de conexiones hacia
PostgreSQL (Neon) con SSL obligatorio.

Responsabilidades:
- Inicializacion y verificacion de salud del pool al arranque.
- Cierre ordenado del pool al apagar el servidor.
- Dependency injection para FastAPI (get_db_connection).

Seguridad:
- La URL de conexion se construye en runtime (ver core/config.py).
- SSL forzado via sslmode=require + channel_binding=require.
- Conexiones devueltas automaticamente al pool via async context manager.
"""

from typing import AsyncGenerator

from fastapi import Request, HTTPException, status
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from app.core.config import get_database_url


async def create_db_pool() -> AsyncConnectionPool:
    """
    Crea e inicializa el pool asincrono de conexiones PostgreSQL.
    
    Configuracion:
    - min_size=1: Mantiene al menos 1 conexion activa (warm start).
    - max_size=10: Limite superior de conexiones concurrentes.
    - timeout=30s: Tiempo maximo de espera para obtener conexion del pool.
    - Verifica la salud de la conexion initial con pool.check().
    
    Returns:
        AsyncConnectionPool listo para servir requests.
    
    Raises:
        RuntimeError: Si las variables PG* estan ausentes.
        OperationalError: Si Neon no es alcanzable (red/SSL).
    """
    database_url = get_database_url()

    pool = AsyncConnectionPool(
        conninfo=database_url,
        min_size=1,
        max_size=10,
        timeout=30.0,
    )
    await pool.open()
    # Verificacion de salud: falla rapido si Neon no responde
    await pool.check()
    return pool


async def close_db_pool(pool: AsyncConnectionPool) -> None:
    """Cierra ordenadamente todas las conexiones del pool."""
    await pool.close()


async def get_db_connection(
    request: Request,
) -> AsyncGenerator[AsyncConnection, None]:
    """
    Dependency de FastAPI para inyectar una conexion de BD en cualquier endpoint.
    
    Uso en un router:
        @router.get("/recurso")
        async def get_recurso(conn = Depends(get_db_connection)):
            async with conn.cursor() as cur:
                await cur.execute("SELECT ...")
    
    La conexion se devuelve automaticamente al pool al salir del scope.
    
    Raises:
        HTTP 503 si el pool no esta disponible.
    """
    pool: AsyncConnectionPool | None = getattr(request.app.state, "db_pool", None)

    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pool de base de datos no disponible. El servidor puede estar arrancando.",
        )

    async with pool.connection() as conn:
        yield conn
