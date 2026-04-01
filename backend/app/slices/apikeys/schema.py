from pydantic import BaseModel
from typing import List

class ApiKeyCreateRequest(BaseModel):
    name: str

class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    api_key_plain: str
    message: str = "Importante: Proteja esta API Key. NO podrá volver a ser visualizada una vez que cierre este panel."

class ApiKeyListResponse(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: str
    active: bool
