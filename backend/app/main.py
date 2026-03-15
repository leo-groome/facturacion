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

