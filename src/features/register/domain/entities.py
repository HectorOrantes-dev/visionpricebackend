"""Entidades de dominio para el registro de usuarios."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewUser:
    """Datos de entrada validados para crear un usuario."""

    nombre: str
    correo: str
    contrasena_hash: str
    rol_id: int
    telefono: str | None = None


@dataclass
class RegisteredUser:
    """Usuario ya persistido (vista de dominio, sin el hash)."""

    id: int
    nombre: str
    correo: str
    telefono: str | None
    rol_id: int
    rol: str
    activo: bool
    fecha_registro: datetime
