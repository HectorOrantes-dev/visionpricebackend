"""Puerto del repositorio de equipos."""
from abc import ABC, abstractmethod

from src.features.equipos.domain.entities import Equipo, Miembro


class EquipoRepository(ABC):
    @abstractmethod
    async def crear(self, *, nombre: str, propietario_id: int) -> Equipo:
        ...

    @abstractmethod
    async def listar_de(self, propietario_id: int) -> list[Equipo]:
        ...

    @abstractmethod
    async def obtener(self, equipo_id: int) -> Equipo | None:
        ...

    @abstractmethod
    async def usuario_id_por_correo(self, correo: str) -> int | None:
        ...

    @abstractmethod
    async def agregar_miembro(
        self, *, equipo_id: int, usuario_id: int, rol_en_equipo: str | None
    ) -> bool:
        """True si se agregó; False si ya era miembro."""

    @abstractmethod
    async def quitar_miembro(self, *, equipo_id: int, usuario_id: int) -> bool:
        ...

    @abstractmethod
    async def listar_miembros(self, equipo_id: int) -> list[Miembro]:
        ...
