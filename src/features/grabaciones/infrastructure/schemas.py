"""Schemas HTTP de la feature grabaciones."""
from datetime import datetime

from pydantic import BaseModel, Field


class GrabacionOut(BaseModel):
    id: int
    usuario_id: int
    proyecto_id: int | None
    object_storage_key: str | None
    estado_sincronizacion: str


class GrabacionResumenOut(BaseModel):
    id: int
    proyecto_id: int | None
    estado_sincronizacion: str
    duracion_segundos: int | None
    fecha_grabacion: datetime
    fecha_sincronizacion: datetime | None
    tiene_transcripcion: bool


class GrabacionDetalleOut(BaseModel):
    id: int
    proyecto_id: int | None
    estado_sincronizacion: str
    duracion_segundos: int | None
    fecha_grabacion: datetime
    fecha_sincronizacion: datetime | None
    transcripcion: str | None
    modelo_voice_to_text: str | None
    confianza: float | None
    extraccion_json: dict | None
    version_modelo: str | None


class MLCallbackRequest(BaseModel):
    """Payload que envía el microservicio de ML al terminar de procesar."""

    grabacion_id: int
    texto: str
    parametros_json: dict
    object_storage_key: str | None = None
    modelo_voice_to_text: str | None = Field(default=None, max_length=100)
    confianza: float | None = Field(default=None, ge=0, le=1)
    version_modelo: str | None = Field(default=None, max_length=50)


class MLCallbackResponse(BaseModel):
    received: bool = True
    grabacion_id: int
