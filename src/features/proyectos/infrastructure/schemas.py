"""Schemas HTTP de la feature proyectos."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Estado = Literal["activo", "finalizado", "cancelado"]


class CrearProyectoRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    direccion: str | None = Field(default=None, max_length=255)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)


class ActualizarProyectoRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
    direccion: str | None = Field(default=None, max_length=255)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    estado: Estado | None = None


class ProyectoOut(BaseModel):
    id: int
    nombre: str
    direccion: str | None
    latitud: float | None
    longitud: float | None
    estado: str
    fecha_creacion: datetime
    total_presupuestos: int
    es_dueno: bool = True  # True = propietario, False = colaborador

