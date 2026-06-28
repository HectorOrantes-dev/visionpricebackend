"""Schemas HTTP de la feature equipos."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CrearEquipoRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)


class EquipoOut(BaseModel):
    id: int
    nombre: str
    propietario_id: int
    fecha_creacion: datetime


class AgregarMiembroRequest(BaseModel):
    correo: EmailStr
    rol_en_equipo: str | None = Field(default=None, max_length=50)


class MiembroOut(BaseModel):
    usuario_id: int
    nombre: str
    correo: EmailStr
    rol_en_equipo: str | None
    fecha_asignacion: datetime


class OkOut(BaseModel):
    ok: bool = True
