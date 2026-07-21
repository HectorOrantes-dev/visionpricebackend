"""Schema rígido de parámetros extraídos por el LLM: piso y pintura.

El microservicio de ML transcribe y hace la interpretación semántica; esta
feature solo define el CONTRATO tipado que su salida (parametros_json, hoy un
dict libre en ExtraccionLLM) debe cumplir para poder cotizarse, y normaliza lo
que llegue a esa forma. Las categorías coinciden 1:1 con
`cotizaciones.domain.reglas_material` (piso/azulejo/zoclo → kit de
instalación; pintura/impermeabilizante → rendimiento).
"""
from dataclasses import dataclass, field


@dataclass
class SuperficieExtraida:
    categoria: str
    area_m2: float | None = None
    largo_m: float | None = None
    ancho_m: float | None = None
    alto_m: float | None = None
    descripcion: str | None = None
    # Piso: porcelanato/laminado/vinílico/madera/concreto pulido.
    # Pintura: mate/satinado/esmalte.
    acabado: str | None = None
    manos_pintura: int | None = None
    requiere_resane: bool = False


@dataclass
class ParametrosExtraidos:
    superficies: list[SuperficieExtraida]
    notas: str | None = None
    advertencias: list[str] = field(default_factory=list)
