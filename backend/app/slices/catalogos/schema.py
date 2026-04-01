from pydantic import BaseModel, Field
from typing import List

class CatalogoItemResponse(BaseModel):
    Value: str = Field(..., alias="Value")
    Name: str = Field(..., alias="Name")

class CatalogoSearchResponse(BaseModel):
    resultados: List[CatalogoItemResponse]
