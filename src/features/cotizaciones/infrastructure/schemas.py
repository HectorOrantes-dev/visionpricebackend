"""Schemas HTTP de la feature cotizaciones."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# --- Cálculo de m² ---
class CalculoRequest(BaseModel):
    grabacion_id: int | None = None
    texto: str | None = None
    # Overrides manuales: se combinan con lo que el regex detectó del texto/
    # transcripción (ej. la altura no se detectó y el usuario la escribe a
    # mano). Solo se reemplaza la dimensión que venga en el override.
    largo_m: float | None = Field(default=None, gt=0)
    ancho_m: float | None = Field(default=None, gt=0)
    alto_m: float | None = Field(default=None, gt=0)
    # Override de área final: para medir una sola superficie (ej. "una pared
    # de 2x2 m") sin pasar por la fórmula de perímetro de cuarto completo.
    piso_m2: float | None = Field(default=None, gt=0)
    paredes_m2: float | None = Field(default=None, gt=0)


class CalculoOut(BaseModel):
    largo_m: float | None
    ancho_m: float | None
    alto_m: float | None
    piso_m2: float | None
    paredes_m2: float | None
    advertencias: list[str]


# --- Productos cercanos ---
class ProductoCercanoOut(BaseModel):
    producto_id: str
    nombre: str
    categoria: str
    unidad: str
    precio_unitario: float
    rendimiento_m2: float | None
    image_url: str | None = None
    proveedor_id: str | None
    proveedor_nombre: str | None
    proveedor_lat: float | None = None
    proveedor_lng: float | None = None
    distancia_km: float | None
    pieza_largo_m: float | None = None
    pieza_ancho_m: float | None = None
    piezas_por_paquete: int | None = None


# --- Crear cotización ---
class ItemRequest(BaseModel):
    producto_id: str
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
    # Monto fijo que el usuario cobra por instalación/servicio. Se agrega como
    # una línea más de la cotización (no depende de proveedores) y se suma al total.
    mano_obra: float | None = Field(default=None, gt=0)


class MaterialReglaOut(BaseModel):
    categoria: str
    metodo_calculo: str          # rendimiento | kit
    requiere_kit: bool
    complementos: list[str]


class SuperficieKitRequest(BaseModel):
    area_m2: float = Field(gt=0)
    principal_producto_id: str  # la loseta (piso/azulejo/zoclo)
    descripcion: str | None = Field(default=None, max_length=150)
    metodo_crucetas: Literal["interseccion", "tradicional", "nivelacion"] = (
        "tradicional"
    )
    adhesivo_producto_id: str | None = None
    cruceta_producto_id: str | None = None
    boquilla_producto_id: str | None = None


class CrearKitRequest(BaseModel):
    proyecto_id: int
    superficies: list[SuperficieKitRequest] = Field(min_length=1)
    mano_obra: float | None = Field(default=None, gt=0)


class LineaOut(BaseModel):
    material_id: str | None
    proveedor_id: str | None
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
    mano_obra: float | None = None
    lineas: list[LineaOut]
