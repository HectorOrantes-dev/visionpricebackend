"""Reglas por tipo de material: ¿es simple o necesita un kit de complementos?

Define, para cada categoría que detecta el motor de IA, cómo debe cotizarse:

  - "rendimiento" (SIMPLE): un solo producto, cantidad = ceil(área / rendimiento_m2).
      Ej: pintura, impermeabilizante. → usar POST /cotizaciones.
  - "kit": producto principal (loseta) + complementos (pegazulejo/cruceta/emboquillado).
      Ej: piso, azulejo, zoclo. → usar POST /cotizaciones/kit.

La app consulta GET /cotizaciones/materiales para saber cómo dibujar la UI de
cada material sin hardcodear las reglas.
"""
from dataclasses import dataclass, field


@dataclass
class ReglaMaterial:
    categoria: str
    metodo_calculo: str          # "rendimiento" | "kit"
    requiere_kit: bool
    complementos: list[str] = field(default_factory=list)


_REGLAS: dict[str, ReglaMaterial] = {
    "piso": ReglaMaterial("piso", "kit", True, ["pegazulejo", "cruceta", "emboquillado"]),
    "azulejo": ReglaMaterial("azulejo", "kit", True, ["pegazulejo", "cruceta", "emboquillado"]),
    "zoclo": ReglaMaterial("zoclo", "kit", True, ["pegazulejo", "cruceta", "emboquillado"]),
    "pintura": ReglaMaterial("pintura", "rendimiento", False),
    "impermeabilizante": ReglaMaterial("impermeabilizante", "rendimiento", False),
}


def regla_de(categoria: str) -> ReglaMaterial:
    """Regla de una categoría. Si no está en el catálogo, se asume SIMPLE."""
    cat = (categoria or "").lower().strip()
    return _REGLAS.get(
        cat, ReglaMaterial(cat or "desconocido", "rendimiento", False)
    )


def todas() -> list[ReglaMaterial]:
    return list(_REGLAS.values())
