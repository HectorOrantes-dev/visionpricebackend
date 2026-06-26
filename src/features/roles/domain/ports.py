"""Puerto del catálogo de roles."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Rol:
    id: int
    nombre: str


class RoleRepository(ABC):
    @abstractmethod
    async def listar(self) -> list[Rol]:
        ...
