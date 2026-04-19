from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class Impuesto(BaseModel):
    tipo: str = Field(..., description="IVA | IEPS | ISR | IVA_RET")
    tasa: Decimal = Field(..., decimal_places=6)
    importe: Decimal = Field(..., decimal_places=2)


class Concepto(BaseModel):
    clave_prod_serv: str = Field(..., description="Clave SAT c_ClaveProdServ")
    clave_unidad: str = Field("H87", description="Clave SAT c_ClaveUnidad (H87=Pieza)")
    descripcion: str = Field(..., description="Descripcion del bien o servicio")
    cantidad: Decimal = Field(..., decimal_places=2)
    valor_unitario: Decimal = Field(..., decimal_places=2)
    importe: Decimal = Field(..., decimal_places=2)
    descuento: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    impuestos: List[Impuesto] = []


class EmisionDraftRequest(BaseModel):
    receptor_rfc: str
    receptor_razon_social: str
    receptor_regimen: str = Field(..., description="Codigo c_RegimenFiscal del receptor")
    receptor_domicilio_fiscal: str = Field(..., description="Codigo postal del domicilio fiscal del receptor")
    receptor_email: Optional[str] = Field(None, description="Correo electronico del receptor para envio del CFDI")
    uso_cfdi: str = Field("G03", description="Codigo c_UsoCFDI (G03=Gastos en general)")
    conceptos: List[Concepto]
    moneda: str = "MXN"
    forma_pago: str = Field("01", description="Codigo c_FormaPago (01=Efectivo)")
    metodo_pago: str = Field("PUE", description="PUE=Pago en una sola exhibicion | PPD=Pago en parcialidades")


class EmisionDraftResponse(BaseModel):
    subtotal: Decimal
    total_impuestos_trasladados: Decimal
    total_impuestos_retenidos: Decimal
    total: Decimal
    preview_json: dict


class EmisionResponse(BaseModel):
    """Respuesta tras timbrar exitosamente un CFDI 4.0."""
    id: str = Field(..., description="UUID local de la factura en nuestra DB")
    folio_fiscal: str = Field(..., description="UUID del timbre fiscal digital del SAT")
    facturama_id: str = Field(..., description="ID interno de Facturama para descargas")
    fecha_emision: str
    receptor_rfc: str
    receptor_razon_social: str
    total: Decimal
    estado: str = "Vigente"


class CancelacionRequest(BaseModel):
    motivo: str = Field(..., pattern="^(01|02|03|04)$", description="Motivo SAT: 01=Error con relacion | 02=Error sin relacion | 03=No se realizo | 04=Operacion nominativa")
    folio_sustituto: Optional[str] = Field(None, description="UUID del CFDI sustituto (obligatorio para motivo 01)")


class FacturaListResponse(BaseModel):
    id: str
    folio_fiscal: Optional[str]
    fecha_emision: Optional[str]
    receptor_rfc: str
    receptor_razon_social: str
    receptor_email: Optional[str]
    total: Decimal
    estado: str


class PaginatedFacturasResponse(BaseModel):
    total_records: int
    page: int
    page_size: int
    data: List[FacturaListResponse]
