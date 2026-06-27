"""Schemas HTTP de la feature notificaciones."""
from datetime import datetime

from pydantic import BaseModel, Field


class NotificacionOut(BaseModel):
    id: int
    tipo: str
    titulo: str
    cuerpo: str
    canal: str
    estado: str
    leida: bool
    referencia_tipo: str | None
    referencia_id: int | None
    fecha_creacion: datetime
    fecha_envio: datetime | None


class EventoRequest(BaseModel):
    """Para que features/microservicios emitan una notificación de negocio."""

    usuario_id: int
    tipo: str = Field(description="suscripcion_*, grabacion_*, presupuesto_listo, ...")
    titulo: str | None = Field(default=None, max_length=150)
    cuerpo: str | None = Field(default=None, max_length=500)
    referencia_tipo: str | None = Field(default=None, max_length=40)
    referencia_id: int | None = None


class JobResultOut(BaseModel):
    por_vencer: int
    vencidas: int


class OkOut(BaseModel):
    ok: bool = True
