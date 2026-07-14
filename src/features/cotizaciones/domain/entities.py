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
    producto_id: str
    nombre: str
    categoria: str
    unidad: str
    precio_unitario: float
    rendimiento_m2: float | None
    image_url: str | None
    proveedor_id: str | None
    proveedor_nombre: str | None
    proveedor_lat: float | None = None
    proveedor_lng: float | None = None
    distancia_km: float | None = None
    # Losetas/cerámica: dimensiones de la pieza (para contar piezas → crucetas).
    pieza_largo_m: float | None = None
    pieza_ancho_m: float | None = None
    # Crucetas / productos vendidos por paquete: unidades por paquete.
    piezas_por_paquete: int | None = None


@dataclass
class LineaCotizacion:
    material_id: str | None
    proveedor_id: str | None
    proveedor_nombre: str | None
    proveedor_distancia: float | None
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

    @property
    def mano_obra(self) -> float | None:
        # La línea de mano de obra no viene de Proveedores, por eso no tiene
        # material_id (ver CrearCotizacion/CrearCotizacionKit).
        for linea in self.lineas:
            if linea.material_id is None:
                return linea.subtotal
        return None


@dataclass
class InfoProyectoPdf:
    proyecto_id: int
    nombre_proyecto: str
    direccion: str | None
    nombre_usuario: str
