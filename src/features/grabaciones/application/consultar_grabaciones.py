"""Casos de uso de consulta de grabaciones (lista + detalle/estado)."""
from src.features.grabaciones.domain.entities import (
    GrabacionDetalle,
    GrabacionResumen,
)
from src.features.grabaciones.domain.ports import GrabacionRepository
from src.shared.errors import NotFound, ValidationError


class ListarGrabaciones:
    def __init__(self, repo: GrabacionRepository) -> None:
        self._repo = repo

    async def execute(self, usuario_id: int) -> list[GrabacionResumen]:
        return await self._repo.listar_de(usuario_id)


class ObtenerGrabacion:
    def __init__(self, repo: GrabacionRepository) -> None:
        self._repo = repo

    async def execute(
        self, grabacion_id: int, usuario_id: int
    ) -> GrabacionDetalle:
        detalle = await self._repo.obtener_detalle(grabacion_id, usuario_id)
        if detalle is None:
            raise NotFound("Grabación no encontrada.")
        return detalle


class EditarTranscripcion:
    """Guarda una corrección del texto de la transcripción (solo dueño)."""

    def __init__(self, repo: GrabacionRepository) -> None:
        self._repo = repo

    async def execute(
        self, grabacion_id: int, usuario_id: int, texto: str
    ) -> GrabacionDetalle:
        if not texto.strip():
            raise ValidationError("El texto no puede estar vacío.")
        ok = await self._repo.actualizar_transcripcion(
            grabacion_id, usuario_id, texto
        )
        if not ok:
            raise NotFound(
                "Grabación no encontrada o aún sin transcripción que editar."
            )
        detalle = await self._repo.obtener_detalle(grabacion_id, usuario_id)
        assert detalle is not None
        return detalle
