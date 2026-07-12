"""Motor de instalación: calcula el KIT completo para colocar loseta/piso/azulejo.

Al colocar una loseta se necesitan materiales complementarios:
  - PRINCIPAL:  la loseta (piso/azulejo/zoclo)  → cajas
  - ADHESIVO:   pegazulejo                       → sacos (por rendimiento m²)
  - CRUCETAS:   separadores                      → paquetes (dependen de las piezas)
  - BOQUILLA:   junta / detallado                → unidades (por rendimiento m²)

Reglas clave (validadas con los números del cliente):
  piezas   = ceil(area / (pieza_largo × pieza_ancho))
  cajas    = ceil(area / rendimiento_m2_caja)        # rendimiento POR UNIDAD DE VENTA
  crucetas = crucetas_por_pieza[metodo] × piezas
  paquetes = ceil(crucetas / piezas_por_paquete)

Método de instalación (crucetas por loseta):
  intersección = 1   ·   tradicional = 4   ·   nivelación = 8
"""
import math
from dataclasses import dataclass

# Crucetas por pieza según el método de colocación.
CRUCETAS_POR_PIEZA = {
    "interseccion": 1,   # una cruceta en cada cruce
    "tradicional": 4,    # cuatro por loseta (una por lado) — DEFAULT del sistema
    "nivelacion": 8,     # clips de nivelación (gran formato)
}


def piezas_necesarias(
    area_m2: float, pieza_largo_m: float, pieza_ancho_m: float, *, merma: float = 0.0
) -> int:
    """Número de losetas para cubrir el área (con merma opcional)."""
    area_pieza = pieza_largo_m * pieza_ancho_m
    if area_pieza <= 0:
        return 0
    return math.ceil(area_m2 * (1 + merma) / area_pieza)


def unidades_por_rendimiento(
    area_m2: float, rendimiento_m2: float, *, merma: float = 0.0
) -> int:
    """Unidades de venta (cajas/sacos/cubetas) por rendimiento m²/unidad."""
    if rendimiento_m2 <= 0:
        return math.ceil(area_m2 * (1 + merma))
    return math.ceil(area_m2 * (1 + merma) / rendimiento_m2)


def crucetas_necesarias(piezas: int, *, metodo: str = "tradicional") -> int:
    por_pieza = CRUCETAS_POR_PIEZA.get(metodo, CRUCETAS_POR_PIEZA["tradicional"])
    return por_pieza * piezas


def paquetes(total_unidades: int, por_paquete: int | None) -> int:
    """Paquetes a comprar dado un total de unidades y cuántas trae cada paquete."""
    if not por_paquete or por_paquete <= 0:
        return total_unidades  # se vende por unidad
    return math.ceil(total_unidades / por_paquete)


@dataclass
class LineaKit:
    rol: str                 # principal | adhesivo | cruceta | boquilla
    producto_id: str
    nombre: str
    cantidad: int            # unidades a comprar (cajas/sacos/paquetes)
    unidad: str
    precio_unitario: float
    subtotal: float
    detalle: str
    piezas: int | None = None
