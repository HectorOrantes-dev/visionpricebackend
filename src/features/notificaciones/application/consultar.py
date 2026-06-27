"""Casos de uso de consulta: listar y marcar como leída."""
from dataclasses import dataclass

from src.features.notificaciones.domain.entities import Notificacion
from src.features.notificaciones.domain.ports import NotificacionRepository
from src.shared.errors import NotFound


class ListarNotificaciones:
    def __init__(self, repo: NotificacionRepository) -> None:
        self._repo = repo

    async def execute(
        self, usuario_id: int, solo_no_leidas: bool = False
    ) -> list[Notificacion]:
        return await self._repo.listar_por_usuario(usuario_id, solo_no_leidas)


@dataclass
class MarcarLeidaCommand:
    notificacion_id: int
    usuario_id: int


class MarcarLeida:
    def __init__(self, repo: NotificacionRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: MarcarLeidaCommand) -> None:
        ok = await self._repo.marcar_leida(cmd.notificacion_id, cmd.usuario_id)
        if not ok:
            raise NotFound("Notificación no encontrada.")
