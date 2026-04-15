"""
Middleware de Rechazo Temprano — Vanta Facturacion
===================================================
Actua como PRIMERA linea de defensa: descarta requests sin header Authorization
ANTES de que FastAPI deserialice el body JSON o ejecute la logica de negocio.

Responsabilidades:
- Verificar PRESENCIA del header `Authorization: Bearer ...` en rutas protegidas.
- Rechazar con 401 inmediatamente si el header falta (sin tocar el body).
- Permitir pre-flights CORS (OPTIONS) y rutas publicas sin token.

Lo que NO hace este middleware:
- NO decodifica ni valida el JWT (eso es responsabilidad de `get_current_tenant`).
- NO inyecta claims en `request.state` (ya no es necesario).

La validacion completa del JWT ocurre en `app/core/dependencies.get_current_tenant`,
que usa `HTTPBearer` de FastAPI y registra el esquema en el spec OpenAPI.
"""

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

# Rutas que no requieren header Authorization.
# /docs, /openapi.json, /redoc se controlan desde main.py via APP_ENV=production.
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
    Middleware ASGI puro para rechazo temprano de requests sin Authorization header.
    Compatible con todos los tipos de request (POST con body, streaming, etc.)
    sin el bug de body-consumption de BaseHTTPMiddleware.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Solo interceptar requests HTTP
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path.rstrip("/") or "/"

        # Permitir pre-flights CORS y rutas publicas
        if path in PUBLIC_ENDPOINTS or request.method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # Rechazo temprano: si no hay header Authorization, cortar antes del handler
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            response = JSONResponse(
                status_code=401,
                content={"detail": "Autorizacion requerida. Formato: Authorization: Bearer <token>"},
            )
            await response(scope, receive, send)
            return

        # Header presente — dejar pasar a FastAPI.
        # La validacion del JWT ocurre en get_current_tenant (Depends/Security).
        await self.app(scope, receive, send)
