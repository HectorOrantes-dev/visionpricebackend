"""Schemas HTTP (request/response) de la feature register."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

RolNombre = Literal[
    "maestro_obra", "contratista", "arquitecto", "ingeniero_civil"
]


class RegisterRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    correo: EmailStr
    contrasena: str = Field(min_length=8, max_length=128)
    rol: RolNombre
    telefono: str | None = Field(default=None, max_length=20)


class RegisteredUserOut(BaseModel):
    id: int
    nombre: str
    correo: EmailStr
    telefono: str | None
    rol: str
    activo: bool
    fecha_registro: datetime


class RegisterResponse(BaseModel):
    usuario: RegisteredUserOut
    two_factor_sent: bool
    message: str
