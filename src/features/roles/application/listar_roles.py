"""Caso de uso: listar los roles disponibles (para el selector del front)."""
from src.features.roles.domain.ports import Rol, RoleRepository


class ListarRoles:
    def __init__(self, repo: RoleRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Rol]:
        return await self._repo.listar()
