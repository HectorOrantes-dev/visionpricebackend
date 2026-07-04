"""Motor de materiales (OE6): convierte m² → cantidad de producto a comprar.

Dos métodos según el producto:

1) LOSETA/CERÁMICA (tiene dimensiones de pieza):
     area_pieza  = pieza_largo_m * pieza_ancho_m
     area_merma  = area_m2 * (1 + merma)          # +8% desperdicio por defecto
     piezas      = ceil(area_merma / area_pieza)
     cajas       = ceil(piezas / piezas_por_caja)   # lo que se compra

2) ADHESIVO/PINTURA/SACO (tiene rendimiento m²/unidad):
     bultos      = ceil(area_m2 / rendimiento_m2)
   (ej: un saco de pegazulejo de 20 kg rinde ~5 m² → bultos = ceil(area/5))

Si el producto no trae ni dimensiones ni rendimiento, se cae a 1 unidad/m².
"""
import math
from dataclasses import dataclass

from src.features.cotizaciones.domain.entities import ProductoCercano


@dataclass
class CalculoMaterial:
    metodo: str            # loseta | rendimiento | area
    area_m2: float
    piezas: int | None     # solo losetas
    cantidad: int          # unidades a comprar (cajas / bultos / piezas)
    unidad: str
    detalle: str           # texto legible del desglose


def calcular_material(
    area_m2: float, producto: ProductoCercano, *, merma: float = 0.08
) -> CalculoMaterial:
    # 1) Loseta: dimensiones de pieza (con merma).
    if producto.pieza_largo_m and producto.pieza_ancho_m:
        area_pieza = producto.pieza_largo_m * producto.pieza_ancho_m
        area_merma = area_m2 * (1 + merma)
        piezas = math.ceil(area_merma / area_pieza) if area_pieza > 0 else 0

        if producto.piezas_por_caja and producto.piezas_por_caja > 0:
            cajas = math.ceil(piezas / producto.piezas_por_caja)
            return CalculoMaterial(
                metodo="loseta",
                area_m2=area_m2,
                piezas=piezas,
                cantidad=cajas,
                unidad=producto.unidad or "caja",
                detalle=(
                    f"{piezas} piezas ≈ {cajas} caja(s) para {area_m2:g} m² "
                    f"(+{int(merma * 100)}% merma)"
                ),
            )
        return CalculoMaterial(
            metodo="loseta",
            area_m2=area_m2,
            piezas=piezas,
            cantidad=piezas,
            unidad=producto.unidad or "pieza",
            detalle=(
                f"{piezas} piezas para {area_m2:g} m² (+{int(merma * 100)}% merma)"
            ),
        )

    # 2) Adhesivo/pintura/saco: rendimiento m²/unidad.
    if producto.rendimiento_m2 and producto.rendimiento_m2 > 0:
        cantidad = math.ceil(area_m2 / producto.rendimiento_m2)
        unidad = producto.unidad or "saco"
        return CalculoMaterial(
            metodo="rendimiento",
            area_m2=area_m2,
            piezas=None,
            cantidad=cantidad,
            unidad=unidad,
            detalle=(
                f"{cantidad} {unidad}(s) para {area_m2:g} m² "
                f"(rinde {producto.rendimiento_m2:g} m²/u)"
            ),
        )

    # 3) Fallback: 1 unidad por m².
    cantidad = math.ceil(area_m2)
    unidad = producto.unidad or "unidad"
    return CalculoMaterial(
        metodo="area",
        area_m2=area_m2,
        piezas=None,
        cantidad=cantidad,
        unidad=unidad,
        detalle=f"{cantidad} {unidad}(es) para {area_m2:g} m²",
    )
