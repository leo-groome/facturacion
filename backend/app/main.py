from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="VantaFacturacion API",
    description="Backend SaaS Multi-tenant (B2B/B2C) - Vertical Slice Architecture.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"],
    allow_credentials=True,
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

app.include_router(emisores_router, prefix=API_PREFIX)
app.include_router(catalogos_router, prefix=API_PREFIX)
app.include_router(facturacion_router, prefix=API_PREFIX)
app.include_router(apikeys_router, prefix=API_PREFIX)
