"""Puertos del registro: persistencia de usuarios y roles."""
from abc import ABC, abstractmethod

from src.features.register.domain.entities import NewUser, RegisteredUser


class RegisterUserRepository(ABC):
    @abstractmethod
    async def email_exists(self, correo: str) -> bool:
        ...

    @abstractmethod
    async def get_role_id(self, nombre: str) -> int | None:
        """Devuelve el id del rol por nombre, o None si no existe."""

    @abstractmethod
    async def create(self, new_user: NewUser) -> RegisteredUser:
        ...
