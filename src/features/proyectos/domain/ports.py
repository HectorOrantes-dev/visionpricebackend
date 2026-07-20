"""Puertos del dominio de proyectos — contratos para la infraestructura."""
from abc import ABC, abstractmethod

from src.features.proyectos.domain.entities import (
    Invitacion,
    Miembro,
    NuevoProyecto,
    Proyecto,
)


class ProyectoRepository(ABC):
    @abstractmethod
    async def crear(self, nuevo: NuevoProyecto) -> Proyecto:
        ...

    @abstractmethod
    async def listar_de(
        self, usuario_id: int, estado: str | None = None
    ) -> list[Proyecto]:
        """Proyectos propios + donde el usuario es colaborador."""

    @abstractmethod
    async def obtener(self, proyecto_id: int, usuario_id: int) -> Proyecto | None:
        """Devuelve el proyecto si el usuario es dueño O colaborador."""

    @abstractmethod
    async def actualizar(
        self, proyecto_id: int, usuario_id: int, cambios: dict
    ) -> Proyecto | None:
        """Solo el dueño puede actualizar."""


# ---------------------------------------------------------------------------
# Membresía
# ---------------------------------------------------------------------------


class MembresiaRepository(ABC):
    @abstractmethod
    async def puede_acceder(self, proyecto_id: int, usuario_id: int) -> bool:
        """True si el usuario es dueño del proyecto O colaborador."""

    @abstractmethod
    async def es_dueno(self, proyecto_id: int, usuario_id: int) -> bool:
        """True si el usuario es el creador del proyecto."""

    @abstractmethod
    async def obtener_dueno(self, proyecto_id: int) -> int | None:
        """usuario_id del dueño del proyecto (None si no existe).

        Se usa para notificar al dueño cuando alguien se une a su proyecto.
        """

    @abstractmethod
    async def agregar(
        self, proyecto_id: int, usuario_id: int, rol: str
    ) -> Miembro:
        """Añade al usuario como colaborador con el rol dado."""

    @abstractmethod
    async def es_miembro(self, proyecto_id: int, usuario_id: int) -> bool:
        """True si ya existe la fila en proyecto_colaboradores."""

    @abstractmethod
    async def listar(self, proyecto_id: int) -> list[Miembro]:
        """Lista todos los colaboradores del proyecto (con nombre y correo)."""

    @abstractmethod
    async def quitar(self, proyecto_id: int, usuario_id: int) -> bool:
        """Elimina al colaborador. Devuelve False si no existía."""


# ---------------------------------------------------------------------------
# Invitaciones
# ---------------------------------------------------------------------------


class InvitacionRepository(ABC):
    @abstractmethod
    async def crear(self, invitacion: Invitacion) -> Invitacion:
        ...

    @abstractmethod
    async def obtener_por_codigo(self, codigo: str) -> Invitacion | None:
        ...

    @abstractmethod
    async def listar_activas_de_proyecto(
        self, proyecto_id: int
    ) -> list[Invitacion]:
        ...

    @abstractmethod
    async def incrementar_usos(self, invitacion_id: int) -> None:
        ...

    @abstractmethod
    async def revocar(self, invitacion_id: int) -> bool:
        """Cambia estado a 'revocada'. Devuelve False si no existe."""

    @abstractmethod
    async def codigo_existe(self, codigo: str) -> bool:
        """Verifica unicidad antes de persistir."""


# ---------------------------------------------------------------------------
# Correo (adaptador externo)
# ---------------------------------------------------------------------------


class CorreoPort(ABC):
    @abstractmethod
    async def enviar(self, correo: str, asunto: str, cuerpo: str) -> None:
        """Falla silenciosamente (log) si el micro no responde.
        El código de invitación ya fue creado; el correo es informativo.
        """
