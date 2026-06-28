"""Puerto del repositorio de proyectos."""
from abc import ABC, abstractmethod

from src.features.proyectos.domain.entities import NuevoProyecto, Proyecto


class ProyectoRepository(ABC):
    @abstractmethod
    async def crear(self, nuevo: NuevoProyecto) -> Proyecto:
        ...

    @abstractmethod
    async def listar_de(
        self, usuario_id: int, estado: str | None = None
    ) -> list[Proyecto]:
        """Historial de proyectos del usuario (con conteo de presupuestos)."""

    @abstractmethod
    async def obtener(self, proyecto_id: int, usuario_id: int) -> Proyecto | None:
        ...

    @abstractmethod
    async def actualizar(
        self, proyecto_id: int, usuario_id: int, cambios: dict
    ) -> Proyecto | None:
        ...
