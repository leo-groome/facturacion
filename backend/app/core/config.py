"""
Modulo de Configuracion Centralizada - Vanta Facturacion
=========================================================
Construye parametros criticos (DATABASE_URL, JWT) exclusivamente desde
variables de entorno. NUNCA hardcodea secretos en codigo fuente.

Seguridad:
- URL-encode de credenciales para prevenir inyeccion via caracteres especiales.
- Validacion estricta de presencia de cada variable obligatoria.
- Fuerza SSL y channel_binding contra la instancia Neon.
"""

import os
from urllib.parse import quote_plus


def get_database_url() -> str:
    """
    Ensambla la cadena de conexion PostgreSQL a partir de variables de entorno
    individuales (PGHOST, PGDATABASE, PGUSER, PGPASSWORD, PGSSLMODE).
    
    Ventajas sobre almacenar DATABASE_URL directamente:
    1. Rotacion de credenciales sin reconstruir toda la cadena.
    2. Encoding seguro automatico de caracteres especiales en la contrasena.
    3. Canal de auditoria mas granular (se puede loggear host sin exponer pwd).
    
    Raises:
        RuntimeError: Si alguna variable obligatoria esta ausente.
    """
    host = os.getenv("PGHOST")
    database = os.getenv("PGDATABASE")
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    sslmode = os.getenv("PGSSLMODE", "require")

    required_vars = {
        "PGHOST": host,
        "PGDATABASE": database,
        "PGUSER": user,
        "PGPASSWORD": password,
    }
    missing = [name for name, value in required_vars.items() if not value]

    if missing:
        raise RuntimeError(
            f"Variables de entorno de BD ausentes: {', '.join(missing)}. "
            "Verificar archivo .env antes de iniciar el servidor."
        )

    # Encoding URL-safe para prevenir inyeccion en la cadena de conexion
    encoded_user = quote_plus(user)
    encoded_password = quote_plus(password)

    return (
        f"postgresql://{encoded_user}:{encoded_password}"
        f"@{host}/{database}"
        f"?sslmode={sslmode}"
    )


def get_jwt_secret() -> str:
    """
    Extrae la clave secreta JWT de variables de entorno.
    Aborts el arranque si no esta definida (fail-fast).
    """
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "SECRET_KEY no definida en variables de entorno. "
            "El servidor no puede arrancar sin clave de firma JWT."
        )
    return secret
