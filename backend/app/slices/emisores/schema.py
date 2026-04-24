from pydantic import BaseModel, ConfigDict, Field


class CSDUploadResponse(BaseModel):
    message: str = Field(..., description="Status del proceso de carga y validación")
    rfc: str = Field(..., description="RFC extraido del CSD subido")
    regimen_fiscal: str = Field(..., description="Codigo c_RegimenFiscal SAT del emisor (ej. 601, 612, 626)")

    model_config = ConfigDict(from_attributes=True)


class EmisorMeResponse(BaseModel):
    rfc: str
    regimen_fiscal: str
    es_resico: bool = Field(..., description="True si el régimen es 626 (RESICO)")
    facturama_synced: bool

    model_config = ConfigDict(from_attributes=True)
