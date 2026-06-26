"""Puerto (interfaz) del segundo factor de autenticación.

El dominio sólo conoce este contrato; quién lo implementa (el microservicio
2FA por HTTP, un mock en tests, etc.) es indiferente.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TwoFactorResult:
    valid: bool
    reason: str  # ok | no_active_code | expired | invalid_code


class TwoFactorPort(ABC):
    @abstractmethod
    async def send_code(self, email: str) -> None:
        """Genera y envía un código al correo del usuario."""

    @abstractmethod
    async def verify_code(self, email: str, code: str) -> TwoFactorResult:
        """Valida el código que escribió el usuario."""
