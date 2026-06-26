"""Entidades de dominio del login/register con Google."""
from dataclasses import dataclass


@dataclass
class GoogleIdentity:
    """Datos verificados del id_token de Google."""

    sub: str          # identificador estable del usuario en Google
    email: str
    nombre: str
    email_verified: bool


@dataclass
class GoogleUser:
    """Usuario de la BD relevante para emitir el token."""

    id: int
    correo: str
    rol: str
    activo: bool
    google_sub: str | None
