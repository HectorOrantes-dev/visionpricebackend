"""Puertos de la feature google_auth."""
from abc import ABC, abstractmethod

from src.features.google_auth.domain.entities import GoogleIdentity, GoogleUser


class GoogleIdentityVerifier(ABC):
    """Verifica el id_token de Google (firma, aud, iss, exp)."""

    @abstractmethod
    def verify(self, id_token: str) -> GoogleIdentity:
        ...


class GoogleUserRepository(ABC):
    @abstractmethod
    async def get_by_correo(self, correo: str) -> GoogleUser | None:
        ...

    @abstractmethod
    async def get_role_id(self, nombre: str) -> int | None:
        ...

    @abstractmethod
    async def crear_google(
        self, *, nombre: str, correo: str, rol_id: int, google_sub: str
    ) -> GoogleUser:
        ...

    @abstractmethod
    async def vincular_google(self, usuario_id: int, google_sub: str) -> None:
        """Asocia un google_sub a una cuenta existente (si aún no lo tiene)."""
