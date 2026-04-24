import base64
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_current_tenant
from .schema import CatalogoItemResponse, CatalogoSearchResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalogos", tags=["Catalogos SAT"])

# Cache con TTL de 30 minutos para evitar rate limiting de Facturama
CACHE_TTL = timedelta(minutes=30)
_CACHE: Dict[str, Tuple[datetime, CatalogoSearchResponse]] = {}


def _get_facturama_headers() -> dict:
    user = os.getenv("FACTURAMA_USER", "")
    password = os.getenv("FACTURAMA_PASSWORD", "")
    encoded = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def _cache_get(key: str):
    if key in _CACHE:
        ts, data = _CACHE[key]
        if datetime.now() - ts < CACHE_TTL:
            return data
        del _CACHE[key]
    return None


def _cache_set(key: str, data: CatalogoSearchResponse):
    _CACHE[key] = (datetime.now(), data)


async def _fetch_catalog(facturama_path: str, cache_key: str) -> CatalogoSearchResponse:
    """
    Proxy generico hacia la API de catalogos de Facturama con cache TTL.
    Retorna lista de {Value, Name}.
    """
    cached = _cache_get(cache_key)
    if cached:
        return cached

    base_url = os.getenv("FACTURAMA_API_URL", "https://apisandbox.facturama.mx")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{base_url}{facturama_path}",
                headers=_get_facturama_headers(),
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout conectando a Facturama (catálogos SAT)")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error de red con Facturama: {e}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Error Facturama Catalogo [{response.status_code}]: {response.text}",
        )
    data = response.json()

    resultados = [
        CatalogoItemResponse(Value=item.get("Value"), Name=item.get("Name"))
        for item in data
    ]
    result = CatalogoSearchResponse(resultados=resultados)
    _cache_set(cache_key, result)
    return result


async def _fetch_catalog_search(
    facturama_path: str, keyword: str, cache_key: str
) -> CatalogoSearchResponse:
    """Proxy con parametro de busqueda (keyword) y cache TTL."""
    cached = _cache_get(cache_key)
    if cached:
        return cached

    base_url = os.getenv("FACTURAMA_API_URL", "https://apisandbox.facturama.mx")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{base_url}{facturama_path}",
                params={"keyword": keyword},
                headers=_get_facturama_headers(),
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout conectando a Facturama (catálogos SAT)")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error de red con Facturama: {e}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Error Facturama [{response.status_code}]: {response.text}",
        )
    data = response.json()

    resultados = [
        CatalogoItemResponse(Value=item.get("Value"), Name=item.get("Name"))
        for item in data
    ]
    result = CatalogoSearchResponse(resultados=resultados)
    _cache_set(cache_key, result)
    return result


# ---------------------------------------------------------------------------
# Productos y Servicios (busqueda por keyword)
# ---------------------------------------------------------------------------

@router.get("/prodserv", response_model=CatalogoSearchResponse)
async def buscar_prod_serv(
    keyword: str = Query(..., min_length=3, description="Palabra clave SAT c_ClaveProdServ"),
    tenant: dict = Depends(get_current_tenant),
):
    """Busca claves de Productos y Servicios SAT (c_ClaveProdServ)."""
    return await _fetch_catalog_search(
        "/catalogs/ProductsOrServices",
        keyword,
        f"prodserv_{keyword.lower()}",
    )


# ---------------------------------------------------------------------------
# Unidades de Medida
# ---------------------------------------------------------------------------

@router.get("/unidades", response_model=CatalogoSearchResponse)
async def buscar_unidades(
    keyword: str = Query(..., min_length=2, description="Palabra clave c_ClaveUnidad"),
    tenant: dict = Depends(get_current_tenant),
):
    """Busca unidades de medida SAT (c_ClaveUnidad). Ej: H87=Pieza, E48=Servicio."""
    return await _fetch_catalog_search(
        "/catalogs/Units",
        keyword,
        f"unidades_{keyword.lower()}",
    )


# ---------------------------------------------------------------------------
# Formas de Pago
# ---------------------------------------------------------------------------

@router.get("/formas-pago", response_model=CatalogoSearchResponse)
async def listar_formas_pago(
    tenant: dict = Depends(get_current_tenant),
):
    """Lista todas las formas de pago SAT (c_FormaPago). Ej: 01=Efectivo, 03=Transferencia."""
    return await _fetch_catalog("/catalogs/PaymentForms", "formas_pago")


# ---------------------------------------------------------------------------
# Metodos de Pago
# ---------------------------------------------------------------------------

@router.get("/metodos-pago", response_model=CatalogoSearchResponse)
async def listar_metodos_pago(
    tenant: dict = Depends(get_current_tenant),
):
    """Lista metodos de pago SAT (c_MetodoPago). PUE=Pago unico | PPD=Pago en parcialidades."""
    return await _fetch_catalog("/catalogs/PaymentMethods", "metodos_pago")


# ---------------------------------------------------------------------------
# Usos CFDI
# ---------------------------------------------------------------------------

@router.get("/usos-cfdi", response_model=CatalogoSearchResponse)
async def listar_usos_cfdi(
    regimen: str | None = Query(None, pattern=r"^6\d{2}$", description="Codigo c_RegimenFiscal para filtrar usos permitidos (Anexo 20 SAT)"),
    tenant: dict = Depends(get_current_tenant),
):
    """
    Lista los usos CFDI del receptor (c_UsoCFDI). Si se pasa `regimen`, filtra solo
    los usos compatibles con ese regimen segun la matriz del Anexo 20 SAT.
    """
    catalogo = await _fetch_catalog("/catalogs/CfdiUses", "usos_cfdi")
    if not regimen:
        return catalogo

    from app.slices.facturacion.calculo import usos_cfdi_permitidos
    permitidos = set(usos_cfdi_permitidos(regimen))
    filtrados = [item for item in catalogo.resultados if item.Value in permitidos]
    return CatalogoSearchResponse(resultados=filtrados)


# ---------------------------------------------------------------------------
# Regimenes Fiscales
# ---------------------------------------------------------------------------

@router.get("/regimenes", response_model=CatalogoSearchResponse)
async def listar_regimenes(
    tenant: dict = Depends(get_current_tenant),
):
    """Lista regimenes fiscales SAT (c_RegimenFiscal). Ej: 601=General de Ley Personas Morales."""
    return await _fetch_catalog("/catalogs/FiscalRegimes", "regimenes")
