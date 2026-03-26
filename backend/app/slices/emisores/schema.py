from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class CSDUploadResponse(BaseModel):
    message: str = Field(..., description="Status del proceso de carga y validación")
    rfc: str = Field(..., description="RFC extraido del CSD subido")

    model_config = ConfigDict(from_attributes=True)
