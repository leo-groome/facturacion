from pydantic import BaseModel, Field
from typing import Optional

class UserSignup(BaseModel):
    nombre_empresa: str
    rfc: str = Field(..., min_length=12, max_length=13, description="RFC debe ser de 12 a 13 caracteres")
    password: str

class UserLogin(BaseModel):
    rfc: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
