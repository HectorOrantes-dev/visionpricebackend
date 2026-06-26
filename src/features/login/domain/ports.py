"""Puertos de persistencia del login."""
from abc import ABC, abstractmethod

from src.features.login.domain.entities import AuthUser, DesafioPendiente


class LoginUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, correo: str) -> AuthUser | None:
        ...


class TwoFactorChallengeRepository(ABC):
    """Estado de los desafíos 2FA en la API principal (no guarda el código)."""

    @abstractmethod
    async def crear(
        self,
        *,
        correo: str,
        usuario_id: int | None,
        proposito: str,
        ip_origen: str | None,
    ) -> None:
        ...

    @abstractmethod
    async def obtener_pendiente(self, correo: str) -> DesafioPendiente | None:
        """Desafío pendiente más reciente del correo (o None)."""

    @abstractmethod
    async def actualizar(
        self,
        desafio_id: int,
        *,
        estado: str,
        intentos: int,
        verificado: bool = False,
    ) -> None:
        """Persiste el nuevo estado/intentos del desafío."""
