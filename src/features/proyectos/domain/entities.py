"""Entidades de dominio de proyectos."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NuevoProyecto:
    usuario_id: int
    nombre: str
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None


@dataclass
class Proyecto:
    id: int
    usuario_id: int
    nombre: str
    direccion: str | None
    latitud: float | None
    longitud: float | None
    estado: str
    fecha_creacion: datetime
    total_presupuestos: int = 0
