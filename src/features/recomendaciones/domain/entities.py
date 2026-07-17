"""Entidades de dominio del sistema de recomendación de kits.

Dos preguntas, dos modelos (ver domain/ports.py):
  1) ¿Esta obra necesita un kit (piso/azulejo/zoclo) o es simple (pintura/
     impermeabilizante)? → árbol de decisión (Gini).
  2) Si necesita kit: en esta zona, ¿qué complementos y método de junta se
     usaron en obras similares? → K-NN geográfico.
"""
from dataclasses import dataclass, field
from typing import Literal

TipoKit = Literal["kit", "rendimiento"]
MetodoCrucetas = Literal["interseccion", "tradicional", "nivelacion"]


@dataclass
class Obra:
    """Una fila del historial (sintético o real) usado para entrenar."""
    obra_id: int
    lat: float
    lng: float
    zona_nombre: str
    categoria: str
    area_m2: float
    tipo_kit: TipoKit
    metodo_crucetas: MetodoCrucetas | None = None
    complementos_usados: list[str] = field(default_factory=list)
    # De dónde salió esta fila — para poder reportar cuánto del entrenamiento
    # es señal real vs. relleno sintético (ver EntrenarModelos).
    origen: Literal["real", "sintetico"] = "sintetico"


@dataclass
class ObraNueva:
    """Lo que manda el cliente para pedir una recomendación."""
    lat: float
    lng: float
    categoria: str
    area_m2: float
    # Si se manda, la recomendación queda ligada a esta obra — permite luego
    # cruzarla con la cotización que efectivamente se cree ahí.
    proyecto_id: int | None = None


@dataclass
class RecomendacionKit:
    tipo_kit: TipoKit
    confianza_tipo_kit: float
    complementos_recomendados: list[str]
    metodo_crucetas_recomendado: MetodoCrucetas | None
    zona_referencia: str | None
    n_obras_similares: int
    # Id de la fila persistida en recomendaciones_uso (None si aún no se
    # guardó — lo setea el caso de uso después de construir el resultado).
    recomendacion_id: int | None = None
