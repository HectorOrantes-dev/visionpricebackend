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
class ResultadoML:
    """Lo que devuelve el microservicio de ML por el webhook."""

    grabacion_id: int
    texto: str
    parametros_json: dict
    object_storage_key: str | None = None
    modelo_voice_to_text: str | None = None
    confianza: float | None = None
    version_modelo: str | None = None
