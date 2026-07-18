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
    es_dueno: bool = True  # True = propietario, False = colaborador


@dataclass
class Miembro:
    """Colaborador de un proyecto (entrada en proyecto_colaboradores)."""

    proyecto_id: int
    usuario_id: int
    rol_en_proyecto: str | None
    fecha_asignacion: datetime
    nombre: str = ""
    correo: str = ""


@dataclass
class Invitacion:
    """Código de invitación multiuso a un proyecto."""

    id: int
    proyecto_id: int
    codigo: str
    rol_en_proyecto: str
    estado: str  # activa | expirada | revocada
    usos: int
    invitado_por: int
    fecha_creacion: datetime
    fecha_expiracion: datetime

