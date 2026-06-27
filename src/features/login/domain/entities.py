"""Entidades de dominio del login."""
from dataclasses import dataclass


@dataclass
class DesafioReciente:
    """Desafío 2FA más reciente para un correo (cualquier estado)."""

    id: int
    intentos: int
    estado: str  # pendiente | verificado | bloqueado | expirado


@dataclass
class AuthUser:
    """Proyección del usuario necesaria para autenticar y emitir el token."""

    id: int
    nombre: str
    correo: str
    contrasena_hash: str
    rol: str
    activo: bool
