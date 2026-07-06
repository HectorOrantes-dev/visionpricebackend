"""Puertos de la feature grabaciones."""
from abc import ABC, abstractmethod

from src.features.grabaciones.domain.entities import (
    Grabacion,
    GrabacionDetalle,
    GrabacionResumen,
    NuevaGrabacion,
    ResultadoML,
)


class GrabacionRepository(ABC):
    @abstractmethod
    async def crear(self, nueva: NuevaGrabacion) -> Grabacion:
        ...

    @abstractmethod
    async def listar_de(self, usuario_id: int) -> list[GrabacionResumen]:
        ...

    @abstractmethod
    async def obtener_detalle(
        self, grabacion_id: int, usuario_id: int
    ) -> GrabacionDetalle | None:
        ...

    @abstractmethod
    async def actualizar_transcripcion(
        self, grabacion_id: int, usuario_id: int, texto: str
    ) -> bool:
        """Edita el texto de la transcripción (solo dueño). False si no aplica."""

    @abstractmethod
    async def marcar_enviada(
        self, grabacion_id: int, object_storage_key: str | None
    ) -> None:
        """Tras subir el audio al microservicio: estado=procesando."""

    @abstractmethod
    async def eliminar(self, grabacion_id: int) -> None:
        """Borra la grabación (rollback si falla el envío al ML)."""

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
