"""Generador de obras sintéticas para entrenar los modelos.

No hay datos reales de "qué se cotizó en qué zona" todavía (el sistema es
nuevo), así que este generador construye un histórico plausible a partir de:
  - las categorías y reglas REALES del sistema (reglas_material.py: piso/
    azulejo/zoclo → kit; pintura/impermeabilizante → rendimiento),
  - medidas de pieza y piezas_por_paquete típicas de catálogo de ferretería,
  - zonas geográficas reales de Chiapas (donde ya se vieron cotizaciones).

Cuando haya cotizaciones reales, este módulo se reemplaza por un adaptador de
ObrasDataset que lee `presupuestos` + `detalle_presupuesto` — la interfaz
(domain/ports.py: ObrasDataset) no cambia.
"""
import random

from src.features.cotizaciones.domain.reglas_material import todas as reglas_todas
from src.features.recomendaciones.domain.entities import Obra
from src.features.recomendaciones.domain.ports import ObrasDataset

# Zonas reales donde ya hay actividad (Chiapas). lat/lng son el centro de la
# zona; cada obra sintética se dispersa unos ~5 km alrededor con ruido gaussiano.
_ZONAS = [
    ("Tuxtla Gutiérrez", 16.7833850, -93.0914326),
    ("San Cristóbal de las Casas", 16.7370, -92.6376),
    ("Tapachula", 14.9028, -92.2528),
    ("Comitán", 16.2500, -92.1333),
]

# Medidas de pieza típicas por categoría (largo_m, ancho_m, piezas_por_paquete).
_PIEZAS_KIT = {
    "piso": [(0.60, 0.60, 4), (0.30, 0.30, 11), (0.45, 0.45, 6)],
    "azulejo": [(0.25, 0.40, 5), (0.20, 0.30, 8), (0.30, 0.30, 11)],
    "zoclo": [(0.10, 1.20, 10), (0.08, 1.00, 12)],
}

_METODOS_CRUCETAS = ["interseccion", "tradicional", "nivelacion"]
# Probabilidad de que cada complemento SÍ se haya usado en una obra de kit
# (el pegazulejo es casi obligatorio; emboquillador a veces se cotiza aparte).
# Nombres iguales a las categorías reales de Proveedores (dataset_real.py) —
# si no coinciden, el K-NN cuenta "boquilla" y "emboquillador" como cosas
# distintas y diluye el voto en vez de sumarlo.
_PROB_COMPLEMENTO = {"pegazulejo": 0.95, "cruceta": 0.90, "emboquillador": 0.72}

# Distribución de categorías por obra: kits (piso/azulejo/zoclo) vs simples
# (pintura/impermeabilizante) — la pintura es, por lejos, la más cotizada.
_PESOS_CATEGORIA = {
    "pintura": 0.45,
    "impermeabilizante": 0.10,
    "piso": 0.20,
    "azulejo": 0.18,
    "zoclo": 0.07,
}


def _area_tipica(categoria: str, rng: random.Random) -> float:
    rangos = {
        "pintura": (8, 60),
        "impermeabilizante": (10, 120),
        "piso": (6, 80),
        "azulejo": (3, 30),
        "zoclo": (5, 40),
    }
    lo, hi = rangos.get(categoria, (5, 50))
    return round(rng.uniform(lo, hi), 2)


def generar_obras(n: int = 1200, semilla: int = 42) -> list[Obra]:
    rng = random.Random(semilla)
    reglas = {r.categoria: r for r in reglas_todas()}
    categorias = list(_PESOS_CATEGORIA.keys())
    pesos = list(_PESOS_CATEGORIA.values())

    obras: list[Obra] = []
    for i in range(1, n + 1):
        zona_nombre, lat0, lng0 = rng.choice(_ZONAS)
        # Ruido ~ hasta 5 km (1 grado ≈ 111 km).
        lat = lat0 + rng.gauss(0, 5 / 111)
        lng = lng0 + rng.gauss(0, 5 / 111)

        categoria = rng.choices(categorias, weights=pesos, k=1)[0]
        regla = reglas.get(categoria)
        es_kit = bool(regla and regla.requiere_kit)
        area = _area_tipica(categoria, rng)

        metodo_crucetas = None
        complementos: list[str] = []
        if es_kit:
            metodo_crucetas = rng.choices(
                _METODOS_CRUCETAS, weights=[0.15, 0.65, 0.20], k=1
            )[0]
            for nombre, prob in _PROB_COMPLEMENTO.items():
                if rng.random() < prob:
                    complementos.append(nombre)

        obras.append(
            Obra(
                obra_id=i,
                lat=round(lat, 6),
                lng=round(lng, 6),
                zona_nombre=zona_nombre,
                categoria=categoria,
                area_m2=area,
                tipo_kit="kit" if es_kit else "rendimiento",
                metodo_crucetas=metodo_crucetas,
                complementos_usados=complementos,
                origen="sintetico",
            )
        )
    return obras


class ObrasDatasetSintetico(ObrasDataset):
    def __init__(self, n: int = 1200, semilla: int = 42) -> None:
        self._n = n
        self._semilla = semilla

    async def cargar(self) -> list[Obra]:
        return generar_obras(self._n, self._semilla)
