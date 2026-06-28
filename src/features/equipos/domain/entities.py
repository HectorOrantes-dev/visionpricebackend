"""Entidades de dominio de equipos."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Equipo:
    id: int
    nombre: str
    propietario_id: int
    fecha_creacion: datetime


@dataclass
class Miembro:
    usuario_id: int
    nombre: str
    correo: str
    rol_en_equipo: str | None
    fecha_asignacion: datetime
