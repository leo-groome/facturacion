"""
Modulo de Dependencias Centralizadas - Vanta Facturacion
=========================================================
Inyeccion de dependencias reutilizables para FastAPI.

Seguridad:
- El tenant_id se extrae EXCLUSIVAMENTE del JWT previamente validado
  por el middleware (request.state), NUNCA de headers manipulables
  por el cliente.
- Previene IDOR (Insecure Direct Object Reference) al garantizar
  que el contexto del tenant es inmutable por el usuario final.
"""

from fastapi import Request, HTTPException, status


async def get_current_tenant(request: Request) -> dict:
    """
    Dependency de FastAPI que extrae el contexto del tenant autenticado.

    El middleware JWTAuthMiddleware ya decodifico el token y deposito
    los claims en request.state. Esta funcion los centraliza y valida.

    Returns:
        dict con claves:
            - tenant_id (str): ID unico del registro en tabla clientes.
            - tenant_org (str): RFC del tenant (organizacion).

    Raises:
        HTTP 401 si el middleware no pudo inyectar el contexto
        (token ausente, expirado o corrupto).
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    tenant_org = getattr(request.state, "tenant_org", None)

    if not tenant_id or not tenant_org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contexto de autenticacion ausente. Token JWT invalido o no proporcionado."
        )

    return {"tenant_id": tenant_id, "tenant_org": tenant_org}
