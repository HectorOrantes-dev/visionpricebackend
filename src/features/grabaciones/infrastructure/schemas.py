"""Schemas HTTP de la feature grabaciones."""
from pydantic import BaseModel, Field


class GrabacionOut(BaseModel):
    id: int
    usuario_id: int
    proyecto_id: int | None
    object_storage_key: str | None
    estado_sincronizacion: str


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
