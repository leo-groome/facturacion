import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from psycopg.rows import dict_row

from app.core.dependencies import get_current_tenant
from app.slices.emisores.facturama_client import FacturamaClient
from .schema import (
    CancelacionRequest,
    EmisionDraftRequest,
    EmisionDraftResponse,
    EmisionResponse,
    PaginatedFacturasResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/facturacion", tags=["Facturacion"])

# Tipos MIME para descarga
_MEDIA_TYPES = {
    "xml": "application/xml",
    "pdf": "application/pdf",
    "zip": "application/zip",
}


# ---------------------------------------------------------------------------
# Preview — calcula totales sin consumir timbre
# ---------------------------------------------------------------------------

@router.post("/preview", response_model=EmisionDraftResponse)
async def preview_factura(
    draft: EmisionDraftRequest,
    tenant: dict = Depends(get_current_tenant),
):
    """
    Valida y calcula el borrador CFDI 4.0 con precision Decimal.
    No llama a Facturama, no consume timbre fiscal.
    """
    subtotal = Decimal("0.00")
    traslados = Decimal("0.00")
    retenciones = Decimal("0.00")

    for concepto in draft.conceptos:
        importe_esperado = (concepto.cantidad * concepto.valor_unitario).quantize(Decimal("0.01"))
        if abs(concepto.importe - importe_esperado) > Decimal("0.01"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Importe del concepto '{concepto.descripcion}' incorrecto. Cantidad x ValorUnitario != Importe.",
            )

        subtotal += concepto.importe - concepto.descuento

        for imp in concepto.impuestos:
            if imp.tipo in ("IVA", "IEPS"):
                traslados += imp.importe
            elif imp.tipo in ("ISR", "IVA_RET"):
                retenciones += imp.importe

    total = subtotal + traslados - retenciones

    return EmisionDraftResponse(
        subtotal=subtotal,
        total_impuestos_trasladados=traslados,
        total_impuestos_retenidos=retenciones,
        total=total,
        preview_json=draft.model_dump(),
    )


# ---------------------------------------------------------------------------
# Emitir — timbra y persiste en DB
# ---------------------------------------------------------------------------

@router.post("/emitir", response_model=EmisionResponse, status_code=status.HTTP_201_CREATED)
async def emitir_factura(
    draft: EmisionDraftRequest,
    request: Request,
    tenant: dict = Depends(get_current_tenant),
):
    """
    Timbra un CFDI 4.0 via Facturama y persiste el resultado en PostgreSQL.
    Si el INSERT falla tras timbrar, el XML se incluye en la respuesta de error
    para que no se pierda el timbre fiscal.
    """
    db_pool = request.app.state.db_pool
    org_id = tenant["tenant_id"]

    # Obtener RFC del emisor registrado para este tenant
    async with db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT rfc FROM emisores WHERE organization_id = %s LIMIT 1",
                (org_id,),
            )
            emisor = await cur.fetchone()

    if not emisor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay un CSD registrado para este tenant. Sube tu certificado en /emisores/csd primero.",
        )

    # Calcular totales (misma logica que preview)
    subtotal = Decimal("0.00")
    traslados = Decimal("0.00")
    retenciones = Decimal("0.00")

    for concepto in draft.conceptos:
        subtotal += concepto.importe - concepto.descuento
        for imp in concepto.impuestos:
            if imp.tipo in ("IVA", "IEPS"):
                traslados += imp.importe
            elif imp.tipo in ("ISR", "IVA_RET"):
                retenciones += imp.importe

    total = subtotal + traslados - retenciones

    # Construir payload CFDI 4.0 para Facturama
    cfdi_payload = {
        "Receiver": {
            "Rfc": draft.receptor_rfc,
            "Name": draft.receptor_razon_social,
            "CfdiUse": draft.uso_cfdi,
            "FiscalRegime": draft.receptor_regimen,
            "TaxZipCode": draft.receptor_domicilio_fiscal,
        },
        "CfdiType": "I",
        "PaymentForm": draft.forma_pago,
        "PaymentMethod": draft.metodo_pago,
        "Currency": draft.moneda,
        "Items": [
            {
                "ProductCode": c.clave_prod_serv,
                "UnitCode": c.clave_unidad,
                "Description": c.descripcion,
                "UnitPrice": float(c.valor_unitario),
                "Quantity": float(c.cantidad),
                "Subtotal": float(c.importe - c.descuento),
                "Discount": float(c.descuento) if c.descuento else None,
                "Total": float(
                    c.importe - c.descuento
                    + sum(i.importe for i in c.impuestos if i.tipo in ("IVA", "IEPS"))
                    - sum(i.importe for i in c.impuestos if i.tipo in ("ISR", "IVA_RET"))
                ),
                "Taxes": [
                    {
                        "Name": imp.tipo.replace("_RET", ""),
                        "Rate": float(imp.tasa),
                        "Total": float(imp.importe),
                        "Base": float(c.importe - c.descuento),
                        "IsRetention": imp.tipo in ("ISR", "IVA_RET"),
                    }
                    for imp in c.impuestos
                ],
            }
            for c in draft.conceptos
        ],
    }

    # Timbrar con Facturama
    client = FacturamaClient()
    try:
        resultado = await client.issue_cfdi(cfdi_payload)
    except Exception:
        logger.exception("Error al timbrar CFDI en Facturama")
        raise HTTPException(status_code=502, detail="Error al comunicarse con Facturama para timbrar.")

    facturama_id = resultado.get("Id") or resultado.get("id", "")
    folio_fiscal = resultado.get("FolioFiscal") or resultado.get("Folio", "")
    fecha_emision = resultado.get("Date") or resultado.get("date", "")
    xml_content = resultado.get("Xml") or resultado.get("xml", "")

    # Persistir en DB — si falla, incluir XML en el error para no perder el timbre
    try:
        async with db_pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    INSERT INTO facturas (
                        organization_id, folio_fiscal, facturama_id, fecha_emision,
                        receptor_rfc, receptor_razon_social, receptor_regimen,
                        receptor_domicilio_fiscal, receptor_email, subtotal,
                        total_impuestos_trasladados, total_impuestos_retenidos, total, xml_content
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        org_id, folio_fiscal, facturama_id, fecha_emision,
                        draft.receptor_rfc, draft.receptor_razon_social, draft.receptor_regimen,
                        draft.receptor_domicilio_fiscal, draft.receptor_email, subtotal,
                        traslados, retenciones, total, xml_content,
                    ),
                )
                row = await cur.fetchone()
                await conn.commit()
    except Exception:
        logger.critical(
            "CFDI timbrado pero INSERT en DB fallo. FolioFiscal=%s FacturamaId=%s XML=%s",
            folio_fiscal, facturama_id, xml_content,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "CFDI timbrado exitosamente pero no pudo guardarse en DB. Guarda el XML.",
                "folio_fiscal": folio_fiscal,
                "facturama_id": facturama_id,
                "xml": xml_content,
            },
        )

    return EmisionResponse(
        id=str(row["id"]),
        folio_fiscal=folio_fiscal,
        facturama_id=facturama_id,
        fecha_emision=fecha_emision,
        receptor_rfc=draft.receptor_rfc,
        receptor_razon_social=draft.receptor_razon_social,
        total=total,
    )


# ---------------------------------------------------------------------------
# Explorador — lista paginada con filtro de estado
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedFacturasResponse)
async def list_facturas(
    request: Request,
    page: int = Query(1, ge=1, description="Numero de pagina (inicia en 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Registros por pagina (max 100)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado: Vigente | Cancelado"),
    tenant: dict = Depends(get_current_tenant),
):
    """
    Retorna el listado paginado de CFDI del tenant autenticado.
    El filtrado por organization_id garantiza aislamiento multitenant (IDOR prevention).
    """
    db_pool = request.app.state.db_pool
    org_id = tenant["tenant_id"]
    offset = (page - 1) * page_size

    # Condicion de filtro de estado (opcional)
    estado_filter = ""
    params_count: list = [org_id]
    params_data: list = [org_id]

    if estado in ("Vigente", "Cancelado"):
        estado_filter = " AND estado = %s"
        params_count.append(estado)
        params_data.append(estado)

    params_data += [page_size, offset]

    async with db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            # Total de registros para paginacion
            await cur.execute(
                f"SELECT COUNT(*) AS total FROM facturas WHERE organization_id = %s{estado_filter}",
                params_count,
            )
            total_records = (await cur.fetchone())["total"]

            # Pagina actual
            await cur.execute(
                f"""
                SELECT id, folio_fiscal, fecha_emision, receptor_rfc,
                       receptor_razon_social, receptor_email, total, estado
                FROM facturas
                WHERE organization_id = %s{estado_filter}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                params_data,
            )
            rows = await cur.fetchall()

    data = [
        {
            "id": str(r["id"]),
            "folio_fiscal": str(r["folio_fiscal"]) if r["folio_fiscal"] else None,
            "fecha_emision": r["fecha_emision"].isoformat() if r["fecha_emision"] else None,
            "receptor_rfc": r["receptor_rfc"],
            "receptor_razon_social": r["receptor_razon_social"],
            "receptor_email": r["receptor_email"],
            "total": r["total"],
            "estado": r["estado"],
        }
        for r in rows
    ]

    return PaginatedFacturasResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        data=data,
    )


# ---------------------------------------------------------------------------
# Descarga — XML / PDF / ZIP como Blob (nunca URL directa)
# ---------------------------------------------------------------------------

@router.get("/{factura_id}/download/{formato}")
async def download_factura(
    factura_id: str,
    formato: str,
    request: Request,
    tenant: dict = Depends(get_current_tenant),
):
    """
    Descarga el XML, PDF o ZIP del CFDI como bytes.
    Valida que la factura pertenezca al tenant antes de servir (IDOR prevention).
    Nunca expone URLs directas de Facturama.
    """
    if formato not in _MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="Formato invalido. Usa: xml | pdf | zip")

    db_pool = request.app.state.db_pool
    org_id = tenant["tenant_id"]

    async with db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT facturama_id FROM facturas WHERE id = %s AND organization_id = %s",
                (factura_id, org_id),
            )
            factura = await cur.fetchone()

    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada en el contexto de esta organizacion.")

    facturama_id = factura["facturama_id"]
    if not facturama_id:
        raise HTTPException(status_code=404, detail="Esta factura no tiene ID de Facturama asociado.")

    client = FacturamaClient()
    try:
        file_bytes = await client.download_cfdi(facturama_id, formato)
    except Exception:
        logger.exception("Error al descargar CFDI de Facturama. facturama_id=%s formato=%s", facturama_id, formato)
        raise HTTPException(status_code=502, detail="Error al obtener el archivo de Facturama.")

    return Response(
        content=file_bytes,
        media_type=_MEDIA_TYPES[formato],
        headers={"Content-Disposition": f"attachment; filename=CFDI_{factura_id}.{formato}"},
    )


# ---------------------------------------------------------------------------
# Cancelacion — motivos SAT 01-04
# ---------------------------------------------------------------------------

@router.post("/{factura_id}/cancelar")
async def cancelar_factura(
    factura_id: str,
    payload: CancelacionRequest,
    request: Request,
    tenant: dict = Depends(get_current_tenant),
):
    """
    Cancela un CFDI ante el SAT via Facturama.
    Verifica propiedad del recurso y estado antes de proceder (IDOR prevention).
    Actualiza el estado en DB tras confirmacion del PAC.
    """
    if payload.motivo == "01" and not payload.folio_sustituto:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El motivo 01 requiere indicar el folio del CFDI que sustituye al cancelado.",
        )

    db_pool = request.app.state.db_pool
    org_id = tenant["tenant_id"]

    # Verificar que la factura existe y pertenece al tenant
    async with db_pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT facturama_id, folio_fiscal, estado FROM facturas WHERE id = %s AND organization_id = %s",
                (factura_id, org_id),
            )
            factura = await cur.fetchone()

    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada en el contexto de esta organizacion.")

    if factura["estado"] == "Cancelado":
        raise HTTPException(status_code=409, detail="La factura ya fue cancelada previamente.")

    facturama_id = factura["facturama_id"]

    # Cancelar en Facturama
    client = FacturamaClient()
    try:
        await client.cancel_cfdi(facturama_id, payload.motivo, payload.folio_sustituto)
    except Exception:
        logger.exception("Error al cancelar CFDI en Facturama. facturama_id=%s", facturama_id)
        raise HTTPException(status_code=502, detail="Error al cancelar con Facturama. Intenta nuevamente.")

    # Actualizar estado en DB
    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE facturas
                SET estado = 'Cancelado',
                    motivo_cancelacion = %s,
                    folio_sustituto = %s,
                    fecha_cancelacion = NOW()
                WHERE id = %s AND organization_id = %s
                """,
                (payload.motivo, payload.folio_sustituto, factura_id, org_id),
            )
            await conn.commit()

    return {
        "message": "Factura cancelada exitosamente.",
        "folio_fiscal": str(factura["folio_fiscal"]) if factura["folio_fiscal"] else None,
        "motivo": payload.motivo,
    }
