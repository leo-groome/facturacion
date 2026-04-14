import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import create_db_pool, close_db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager: inicializa el pool asincrono de conexiones a PostgreSQL (Neon)
    antes de servir requests y lo cierra ordenadamente al apagar el servidor.
    La URL de conexion se construye en runtime desde variables PG* individuales.
    """
    pool = await create_db_pool()
    app.state.db_pool = pool
    yield
    await close_db_pool(pool)

app = FastAPI(
    title="VantaFacturacion API",
    description="Backend SaaS Multi-tenant (B2B/B2C) - Vertical Slice Architecture.",
    version="1.0.0",
    lifespan=lifespan
)

from app.slices.auth.middleware import JWTAuthMiddleware
app.add_middleware(JWTAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/", tags=["Root"])
async def root():
    return JSONResponse(content={"message": "VantaFacturacion API is online."})

# --- Routers ---
API_PREFIX = "/api/v1"

from app.slices.emisores.router import router as emisores_router
from app.slices.catalogos.router import router as catalogos_router
from app.slices.facturacion.router import router as facturacion_router
from app.slices.apikeys.router import router as apikeys_router
from app.slices.auth.router import router as auth_router

app.include_router(emisores_router, prefix=API_PREFIX)
app.include_router(catalogos_router, prefix=API_PREFIX)
app.include_router(facturacion_router, prefix=API_PREFIX)
app.include_router(apikeys_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
