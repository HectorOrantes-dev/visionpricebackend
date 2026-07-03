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

    @abstractmethod
    async def datos_sesion(self, usuario_id: int) -> tuple[str, str] | None:
        """(correo, rol) para emitir el JWT tras el reset; None si no existe."""
