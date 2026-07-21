"""Schemas de la feature account."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ActualizarPerfilRequest(BaseModel):
    """Ambos opcionales: solo se actualiza lo que venga. Pensado para
    completar `nombre`/`telefono` tras el registro simplificado."""

    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    telefono: str | None = Field(default=None, max_length=20)


class PerfilOut(BaseModel):
    id: int
    nombre: str
    correo: EmailStr
    telefono: str | None
    rol: str
    activo: bool
    proveedor_auth: str
    fecha_registro: datetime
    plan_activo: str | None
    vigencia_hasta: datetime | None
