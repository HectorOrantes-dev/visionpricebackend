"""Puerto de persistencia para el restablecimiento de contraseña."""
from abc import ABC, abstractmethod


class PasswordUserRepository(ABC):
    @abstractmethod
    async def id_por_correo(self, correo: str) -> int | None:
        """id del usuario por correo (None si no existe)."""

    @abstractmethod
    async def actualizar_password(
        self, usuario_id: int, contrasena_hash: str
    ) -> None:
        ...
