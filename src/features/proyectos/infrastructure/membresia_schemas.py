"""Schemas HTTP de la feature proyectos (membresía e invitaciones)."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# Los mismos roles del sistema (string abierto para flexibilidad futura).
RolEnProyecto = Literal[
    "maestro_obra", "contratista", "arquitecto", "ingeniero_civil"
]


# ---------------------------------------------------------------------------
# Invitaciones
# ---------------------------------------------------------------------------


class CrearInvitacionRequest(BaseModel):
    rol_en_proyecto: RolEnProyecto = Field(
        ..., description="Rol con el que entrará quien use este código."
    )
    correos: list[EmailStr] = Field(
        default_factory=list,
        description="Correos a los que enviar el código (opcional, máx. 10).",
        max_length=10,
    )


class InvitacionOut(BaseModel):
    id: int
    proyecto_id: int
    codigo: str
    rol_en_proyecto: str
    estado: str
    usos: int
    fecha_creacion: datetime
    fecha_expiracion: datetime


# ---------------------------------------------------------------------------
# Unirse
# ---------------------------------------------------------------------------


class UnirseRequest(BaseModel):
    codigo: str = Field(
        ..., min_length=1, max_length=16, description="Código de invitación."
    )


# ---------------------------------------------------------------------------
# Miembros
# ---------------------------------------------------------------------------


class MiembroOut(BaseModel):
    usuario_id: int
    nombre: str
    correo: str
    rol_en_proyecto: str | None
    fecha_asignacion: datetime


# ---------------------------------------------------------------------------
# Mensaje genérico OK
# ---------------------------------------------------------------------------


class OkOut(BaseModel):
    ok: bool = True
