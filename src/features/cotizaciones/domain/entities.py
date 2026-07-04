"""Entidades de dominio de cotizaciones."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Dimensiones:
    largo_m: float | None = None
    ancho_m: float | None = None
    alto_m: float | None = None


@dataclass
class CalculoAreas:
    largo_m: float | None
    ancho_m: float | None
    alto_m: float | None
    piso_m2: float | None
    paredes_m2: float | None
    advertencias: list[str] = field(default_factory=list)


@dataclass
class ProductoCercano:
    producto_id: int
    nombre: str
    categoria: str
    unidad: str
    precio_unitario: float
    rendimiento_m2: float | None
    proveedor_id: int | None
    proveedor_nombre: str | None
    distancia_km: float | None
    # Para losetas/cerámica (opcional): dimensiones de la pieza y piezas por caja.
    pieza_largo_m: float | None = None
    pieza_ancho_m: float | None = None
    piezas_por_caja: int | None = None


@dataclass
class LineaCotizacion:
    material_id: int | None
    proveedor_id: int | None
    descripcion: str
    cantidad: float
    unidad: str
    precio_unitario: float
    subtotal: float
    # Desglose del cálculo (no se persiste; se muestra en la respuesta/PDF).
    piezas: int | None = None
    area_m2: float | None = None


@dataclass
class Cotizacion:
    id: int
    proyecto_id: int
    usuario_id: int
    estado: str
    total: float
    fecha: datetime
    lineas: list[LineaCotizacion]
