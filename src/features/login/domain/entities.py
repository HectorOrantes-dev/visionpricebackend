"""Entidades de dominio del login."""
from dataclasses import dataclass


@dataclass
class DesafioPendiente:
    """Desafío 2FA pendiente más reciente para un correo."""

    id: int
    intentos: int


@dataclass
class AuthUser:
    """Proyección del usuario necesaria para autenticar y emitir el token."""

    id: int
    nombre: str
    correo: str
    contrasena_hash: str
    rol: str
    activo: bool
