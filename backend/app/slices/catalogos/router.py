from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict
from .schema import CatalogoSearchResponse, CatalogoItemResponse
import httpx
import base64
import os
from app.core.dependencies import get_current_tenant

router = APIRouter(prefix="/catalogos", tags=["Catalogos SAT"])

CATALOGO_CACHE: Dict[str, CatalogoSearchResponse] = {}

@router.get("/prodserv", response_model=CatalogoSearchResponse)
async def buscar_prod_serv(
    keyword: str = Query(..., min_length=3, description="Palabra clave a buscar"),
    tenant: dict = Depends(get_current_tenant)
):
    """
    Proxy asincrono hacia integrador real para Claves ProdServ.
    No se permite simulacion, impacta API externa en produccion.
    Se requiere autenticacion JWT valida (tenant extraido del token).
    """
    cache_key = f"prodserv_{keyword.lower()}"
    if cache_key in CATALOGO_CACHE:
        return CATALOGO_CACHE[cache_key]

    base_url = os.getenv("FACTURAMA_API_URL", "https://apisandbox.facturama.mx")
    user = os.getenv("FACTURAMA_USER", "")
    password = os.getenv("FACTURAMA_PASSWORD", "")
    
    credentials = f"{user}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{base_url}/catalogs/ProductsOrServices",
            params={"keyword": keyword},
            headers={"Authorization": f"Basic {encoded}"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Error Facturama API: {response.text}")
            
        data = response.json()
        
    resultados = []
    for item in data:
        resultados.append(CatalogoItemResponse(Value=item.get("Value"), Name=item.get("Name")))
        
    final_response = CatalogoSearchResponse(resultados=resultados)
    CATALOGO_CACHE[cache_key] = final_response
    return final_response
