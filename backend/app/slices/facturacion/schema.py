from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Impuesto(BaseModel):
    tipo: Literal["IVA", "IEPS", "ISR", "IVA_RET"] = Field(..., description="IVA | IEPS | ISR | IVA_RET")
    tasa: Decimal = Field(..., ge=0, decimal_places=6, description="Tasa en decimal (ej. 0.160000)")
    base: Decimal = Field(..., ge=0, decimal_places=6, description="Base gravable del impuesto")
    importe: Decimal = Field(..., ge=0, decimal_places=6)
    es_retencion: bool = Field(default=False, description="True para ISR/IVA_RET, False para IVA/IEPS trasladados")
    es_exento: bool = Field(default=False, description="IVA exento: tasa 0 sin obligacion de traslado")

    @model_validator(mode="after")
    def _coerce_retencion(self) -> "Impuesto":
        if self.tipo in ("ISR", "IVA_RET") and not self.es_retencion:
            self.es_retencion = True
        return self


class Concepto(BaseModel):
    clave_prod_serv: str = Field(..., pattern=r"^\d{8}$", description="Clave SAT c_ClaveProdServ (8 digitos)")
    clave_unidad: str = Field("H87", min_length=1, max_length=3, description="Clave SAT c_ClaveUnidad (H87=Pieza)")
    descripcion: str = Field(..., min_length=1, max_length=1000)
    cantidad: Decimal = Field(..., gt=0, decimal_places=6)
    valor_unitario: Decimal = Field(..., ge=0, decimal_places=6)
    importe: Decimal = Field(..., ge=0, decimal_places=6, description="cantidad * valor_unitario")
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=6)
    objeto_imp: Literal["01", "02", "03", "04"] = Field(
        "02",
        description="01=No objeto | 02=Si objeto | 03=Si objeto no desglose | 04=Si objeto no causa",
    )
    impuestos: List[Impuesto] = []

    @model_validator(mode="after")
    def _validar_concepto(self) -> "Concepto":
        esperado = (self.cantidad * self.valor_unitario).quantize(Decimal("0.000001"))
        if abs(esperado - self.importe) > Decimal("0.01"):
            raise ValueError(
                f"importe ({self.importe}) debe ser cantidad*valor_unitario ({esperado})"
            )
        if self.descuento > self.importe:
            raise ValueError("El descuento no puede superar el importe del concepto")
        if self.objeto_imp == "02" and not self.impuestos:
            raise ValueError("ObjetoImp=02 requiere al menos un nodo de impuestos (traslado)")
        if self.objeto_imp == "01" and self.impuestos:
            raise ValueError("ObjetoImp=01 (No objeto) no admite nodos de impuestos")
        return self


class EmisionDraftRequest(BaseModel):
    receptor_rfc: str = Field(..., min_length=12, max_length=13)
    receptor_razon_social: str = Field(..., min_length=1, max_length=255)
    receptor_regimen: str = Field(..., pattern=r"^6\d{2}$", description="Codigo c_RegimenFiscal del receptor")
    receptor_domicilio_fiscal: str = Field(..., pattern=r"^\d{5}$", description="Codigo postal 5 digitos")
    receptor_email: Optional[str] = Field(None, description="Correo electronico del receptor para envio del CFDI")
    uso_cfdi: str = Field("G03", description="Codigo c_UsoCFDI validado contra el regimen del receptor")
    conceptos: List[Concepto] = Field(..., min_length=1)
    moneda: str = Field(default="MXN", min_length=3, max_length=3)
    forma_pago: str = Field("01", pattern=r"^(0[1-9]|1[0-9]|2[0-9]|30|99)$", description="Codigo c_FormaPago")
    metodo_pago: Literal["PUE", "PPD"] = "PUE"
    enviar_por_email: bool = Field(default=False, description="Si true, Facturama envia el CFDI al receptor tras timbrar")

    @model_validator(mode="after")
    def _reglas_sat(self) -> "EmisionDraftRequest":
        # Regla SAT: PPD obliga FormaPago=99 (Por definir).
        if self.metodo_pago == "PPD" and self.forma_pago != "99":
            raise ValueError(
                "Cuando el metodo de pago es PPD, la forma de pago debe ser '99' (Por definir)."
            )
        if self.enviar_por_email and not self.receptor_email:
            raise ValueError("enviar_por_email requiere receptor_email.")
        # Normalizar RFC a mayusculas
        self.receptor_rfc = self.receptor_rfc.upper().strip()
        return self


class EmisionDraftResponse(BaseModel):
    subtotal: Decimal
    total_impuestos_trasladados: Decimal
    total_impuestos_retenidos: Decimal
    retencion_resico_isr: Decimal = Field(default=Decimal("0"), description="ISR 1.25% inyectado cuando aplica RESICO PF -> PM")
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
    email_enviado: bool = False


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
