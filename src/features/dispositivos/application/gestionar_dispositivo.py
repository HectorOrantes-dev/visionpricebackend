"""Casos de uso: registrar y eliminar el device token del usuario."""
from dataclasses import dataclass

from src.features.dispositivos.domain.ports import DispositivoRepository


@dataclass
class RegistrarDispositivoCommand:
    usuario_id: int
    token: str
    plataforma: str


class RegistrarDispositivo:
    def __init__(self, repo: DispositivoRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: RegistrarDispositivoCommand) -> None:
        await self._repo.registrar(
            usuario_id=cmd.usuario_id, token=cmd.token, plataforma=cmd.plataforma
        )


@dataclass
class EliminarDispositivoCommand:
    usuario_id: int
    token: str


class EliminarDispositivo:
    def __init__(self, repo: DispositivoRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: EliminarDispositivoCommand) -> None:
        await self._repo.eliminar(usuario_id=cmd.usuario_id, token=cmd.token)
