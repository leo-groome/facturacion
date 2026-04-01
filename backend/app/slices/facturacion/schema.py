from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

class Impuesto(BaseModel):
    tipo: str = Field(..., description="Ej: IVA, ISR, IEPS")
    tasa: Decimal = Field(..., decimal_places=6)
    importe: Decimal = Field(..., decimal_places=2)

class Concepto(BaseModel):
    clave_prod_serv: str
    cantidad: Decimal = Field(..., decimal_places=2)
    valor_unitario: Decimal = Field(..., decimal_places=2)
    importe: Decimal = Field(..., decimal_places=2)
    descuento: Decimal = Field(default=Decimal('0.00'), decimal_places=2)
    impuestos: List[Impuesto] = []

class EmisionDraftRequest(BaseModel):
    receptor_rfc: str
    receptor_razon_social: str
    receptor_regimen: str
    receptor_domicilio_fiscal: str
    conceptos: List[Concepto]
    moneda: str = "MXN"
    forma_pago: str = "01"
    metodo_pago: str = "PUE"

class EmisionDraftResponse(BaseModel):
    subtotal: Decimal
    total_impuestos_trasladados: Decimal
    total_impuestos_retenidos: Decimal
    total: Decimal
    preview_json: dict

class CancelacionRequest(BaseModel):
    folio_fiscal: str = Field(..., description="UUID del CFDI a cancelar")
    motivo: str = Field(..., pattern="^(01|02|03|04)$", description="Motivo de cancelación SAT")
    folio_sustituto: Optional[str] = Field(None, description="UUID del CFDI que sustituye al cancelado (Obligatorio para motivo 01)")

class FacturaListResponse(BaseModel):
    id: str
    folio_fiscal: str
    fecha_emision: str
    receptor_rfc: str
    receptor_razon_social: str
    total: Decimal
    estado: str # "Timbrado", "Cancelado"
    
class PaginatedFacturasResponse(BaseModel):
    total_records: int
    data: List[FacturaListResponse]
