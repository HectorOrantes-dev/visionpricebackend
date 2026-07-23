"""Schemas HTTP de la feature proyectos (membresía e invitaciones)."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ---------------------------------------------------------------------------
# Invitaciones
# ---------------------------------------------------------------------------


class CrearInvitacionRequest(BaseModel):
    # rol_en_proyecto ya NO se manda: se deriva del rol de quien invita
    # (contratista -> maestro_obra; arquitecto/ingeniero_civil -> contratista)
    # para que no se pueda forzar una jerarquía inválida desde el cliente.
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
