"""Puertos de persistencia del login."""
from abc import ABC, abstractmethod

from src.features.login.domain.entities import AuthUser


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
    async def registrar_resultado(self, correo: str, *, exito: bool) -> None:
        """Sobre el desafío pendiente más reciente: suma intento y marca estado."""
