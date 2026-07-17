"""Schemas HTTP de la feature recomendaciones."""
from pydantic import BaseModel, Field


class EntrenarOut(BaseModel):
    n_obras: int
    n_obras_reales: int
    n_obras_sinteticas: int
    accuracy_arbol_tipo_kit: float


class RecomendarKitRequest(BaseModel):
    lat: float
    lng: float
    categoria: str
    area_m2: float = Field(gt=0)
    k: int = Field(default=15, ge=3, le=50)


class RecomendacionKitOut(BaseModel):
    tipo_kit: str
    confianza_tipo_kit: float
    complementos_recomendados: list[str]
    metodo_crucetas_recomendado: str | None
    zona_referencia: str | None
    n_obras_similares: int
