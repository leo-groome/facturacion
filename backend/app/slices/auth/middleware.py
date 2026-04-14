"""
Middleware JWT de Autenticacion - Vanta Facturacion
====================================================
Middleware ASGI puro (sin BaseHTTPMiddleware) para evitar el bug conocido
de Starlette donde BaseHTTPMiddleware bloquea requests POST con body
en combinacion con --reload en Windows.

Seguridad:
- Extrae y valida el JWT de cada request protegido.
- Inyecta tenant_id y tenant_org en request.state para uso seguro downstream.
- Rechaza requests sin token valido con HTTP 401.
- NO usa headers spoofables para determinar el tenant.
"""

import os
import jwt
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import JSONResponse


# Rutas que no requieren autenticacion JWT
PUBLIC_ENDPOINTS = frozenset([
    "/",
    "/api/v1/auth/login",
    "/api/v1/auth/signup",
    "/docs",
    "/openapi.json",
    "/redoc",
])


class JWTAuthMiddleware:
    """
    Middleware ASGI puro para autenticacion JWT.
    Compatible con todos los tipos de request (GET, POST con body, streaming)
    sin el bug de body-consumption de BaseHTTPMiddleware.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Solo interceptar requests HTTP (no websockets, lifespan, etc.)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        # Normalizar path para comparacion
        path = request.url.path.rstrip("/") if request.url.path != "/" else "/"

        # Permitir pre-flights CORS y rutas publicas sin autenticacion
        if path in PUBLIC_ENDPOINTS or request.method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # Extraer y validar header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            response = JSONResponse(
                status_code=401,
                content={"detail": "Mecanismo de autorizacion ausente o con formato erroneo"}
            )
            await response(scope, receive, send)
            return

        token = auth_header.split(" ", 1)[1]
        secret = os.getenv("SECRET_KEY")
        algorithm = os.getenv("ALGORITHM", "HS256")

        if not secret:
            response = JSONResponse(
                status_code=500,
                content={"detail": "Falla critica del backend: SECRET_KEY no configurada"}
            )
            await response(scope, receive, send)
            return

        try:
            payload = jwt.decode(token, secret, algorithms=[algorithm])
            # Inyeccion de contexto multitenant en request.state
            # Estos valores provienen del JWT firmado, NO de headers manipulables
            scope.setdefault("state", {})
            scope["state"]["tenant_id"] = payload.get("id")
            scope["state"]["tenant_org"] = payload.get("org")
        except jwt.ExpiredSignatureError:
            response = JSONResponse(
                status_code=401,
                content={"detail": "Firma JWT expirada"}
            )
            await response(scope, receive, send)
            return
        except jwt.PyJWTError:
            response = JSONResponse(
                status_code=401,
                content={"detail": "Firma JWT corrupta o invalida"}
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
