"""Schemas HTTP de la feature google_auth."""
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

RolNombre = Literal[
    "maestro_obra", "contratista", "arquitecto", "ingeniero_civil"
]


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=10, description="id_token de Google Sign-In")


class GoogleRegisterRequest(BaseModel):
    id_token: str = Field(min_length=10)
    rol: RolNombre


class GoogleTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    correo: EmailStr
    rol: str
    es_nuevo: bool
