"""Entidades de dominio de grabaciones / pipeline de ML."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NuevaGrabacion:
    usuario_id: int
    proyecto_id: int | None
    duracion_segundos: int | None
    hash_archivo: str | None
    fecha_grabacion: datetime


@dataclass
class Grabacion:
    id: int
    usuario_id: int
    proyecto_id: int | None
    object_storage_key: str | None
    estado_sincronizacion: str  # pendiente | procesando | sincronizado | error


@dataclass
class GrabacionResumen:
    """Vista de lista para el historial de audios del usuario."""

    id: int
    proyecto_id: int | None
    estado_sincronizacion: str
    duracion_segundos: int | None
    fecha_grabacion: datetime
    fecha_sincronizacion: datetime | None
    tiene_transcripcion: bool


@dataclass
class GrabacionDetalle:
    """Detalle con el resultado del procesamiento (cuando ya está)."""

    id: int
    proyecto_id: int | None
    estado_sincronizacion: str
    object_storage_key: str | None
    duracion_segundos: int | None
    fecha_grabacion: datetime
    fecha_sincronizacion: datetime | None
    transcripcion: str | None
    modelo_voice_to_text: str | None
    confianza: float | None
    extraccion_json: dict | None
    version_modelo: str | None


@dataclass
class ResultadoML:
    """Lo que devuelve el microservicio de ML por el webhook."""

    grabacion_id: int
    texto: str
    parametros_json: dict
    object_storage_key: str | None = None
    modelo_voice_to_text: str | None = None
    confianza: float | None = None
    version_modelo: str | None = None
