"""Motor de materiales (OE6): convierte m² → cantidad de producto a comprar.

Un solo método principal según el producto:

1) RENDIMIENTO (tiene rendimiento m²/unidad):
     cantidad    = ceil(area_merma / rendimiento_m2)
   (ej: 1 caja de piso rinde 1.44 m² → cajas = ceil(area_merma / 1.44))
   (ej: 1 cubeta de pintura rinde 40 m² → cubetas = ceil(area_merma / 40))

Si el producto no trae rendimiento, se asume 1 unidad por m².
"""
import math
from dataclasses import dataclass

from src.features.cotizaciones.domain.entities import ProductoCercano


@dataclass
class CalculoMaterial:
    metodo: str            # rendimiento | area
    area_m2: float
    piezas: int | None     # se mantiene por compatibilidad
    cantidad: int          # unidades a comprar
    unidad: str
    detalle: str           # texto legible del desglose


def calcular_material(
    area_m2: float, producto: ProductoCercano, *, merma: float = 0.08
) -> CalculoMaterial:
    area_merma = area_m2 * (1 + merma)
    
    # 1) Con rendimiento_m2 universal
    if producto.rendimiento_m2 and producto.rendimiento_m2 > 0:
        cantidad = math.ceil(area_merma / producto.rendimiento_m2)
        unidad = producto.unidad or "unidad"
        return CalculoMaterial(
            metodo="rendimiento",
            area_m2=area_m2,
            piezas=None,
            cantidad=cantidad,
            unidad=unidad,
            detalle=(
                f"{cantidad} {unidad}(s) para {area_m2:g} m² "
                f"(rinde {producto.rendimiento_m2:g} m²/u, +{int(merma * 100)}% merma)"
            ),
        )

    # 2) Fallback: 1 unidad por m².
    cantidad = math.ceil(area_merma)
    unidad = producto.unidad or "unidad"
    return CalculoMaterial(
        metodo="area",
        area_m2=area_m2,
        piezas=None,
        cantidad=cantidad,
        unidad=unidad,
        detalle=f"{cantidad} {unidad}(es) para {area_m2:g} m² (+{int(merma * 100)}% merma)",
    )
