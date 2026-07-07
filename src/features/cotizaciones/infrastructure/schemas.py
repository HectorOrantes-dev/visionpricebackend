"""Schemas HTTP de la feature cotizaciones."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# --- Cálculo de m² ---
class CalculoRequest(BaseModel):
    grabacion_id: int | None = None
    texto: str | None = None


class CalculoOut(BaseModel):
    largo_m: float | None
    ancho_m: float | None
    alto_m: float | None
    piso_m2: float | None
    paredes_m2: float | None
    advertencias: list[str]


# --- Productos cercanos ---
class ProductoCercanoOut(BaseModel):
    producto_id: int
    nombre: str
    categoria: str
    unidad: str
    precio_unitario: float
    rendimiento_m2: float | None
    proveedor_id: int | None
    proveedor_nombre: str | None
    distancia_km: float | None
    pieza_largo_m: float | None = None
    pieza_ancho_m: float | None = None
    piezas_por_caja: int | None = None


# --- Crear cotización ---
class ItemRequest(BaseModel):
    producto_id: int
    # Indica el área con UNA de las dos (area_m2 tiene prioridad):
    area_m2: float | None = Field(default=None, gt=0)
    aplicar_a: Literal["piso", "pared"] | None = None
    descripcion: str | None = Field(default=None, max_length=150)

    @model_validator(mode="after")
    def _tiene_area(self) -> "ItemRequest":
        if self.area_m2 is None and self.aplicar_a is None:
            raise ValueError("Cada ítem necesita area_m2 o aplicar_a.")
        return self


class CrearCotizacionRequest(BaseModel):
    proyecto_id: int
    piso_m2: float | None = Field(default=None, ge=0)
    paredes_m2: float | None = Field(default=None, ge=0)
    items: list[ItemRequest] = Field(min_length=1)


class LineaOut(BaseModel):
    material_id: int | None
    proveedor_id: int | None
    descripcion: str
    cantidad: float
    unidad: str
    precio_unitario: float
    subtotal: float
    piezas: int | None = None
    area_m2: float | None = None


class CotizacionOut(BaseModel):
    id: int
    proyecto_id: int
    estado: str
    total: float
    fecha: datetime
    lineas: list[LineaOut]
