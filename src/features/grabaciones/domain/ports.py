"""Puertos de la feature grabaciones."""
from abc import ABC, abstractmethod

from src.features.grabaciones.domain.entities import (
    Grabacion,
    NuevaGrabacion,
    ResultadoML,
)


class GrabacionRepository(ABC):
    @abstractmethod
    async def crear(self, nueva: NuevaGrabacion) -> Grabacion:
        ...

    @abstractmethod
    async def marcar_enviada(
        self, grabacion_id: int, object_storage_key: str | None
    ) -> None:
        """Tras subir el audio al microservicio: estado=procesando."""

    @abstractmethod
    async def guardar_resultado_ml(self, resultado: ResultadoML) -> None:
        """Persiste transcripción + extracción y marca estado=sincronizado.

        Debe ser idempotente: si ya existe transcripción/extracción para esa
        grabación, no duplica (el webhook puede reintentarse).
        """


class AudioSubmissionPort(ABC):
    """Puerto hacia el microservicio que ingiere y procesa el audio."""

    @abstractmethod
    async def submit_audio(
        self,
        *,
        grabacion_id: int,
        user_hash: str,
        proyecto_id: int | None,
        filename: str,
        audio: bytes,
        content_type: str,
    ) -> dict:
        ...
