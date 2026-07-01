"""Schemas de la feature account."""
from datetime import datetime

from pydantic import BaseModel, EmailStr


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
