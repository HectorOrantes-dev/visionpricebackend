"""Schemas HTTP de la feature recomendaciones."""
from pydantic import BaseModel, Field

from src.features.cotizaciones.infrastructure.schemas import ProductoCercanoOut


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
    # Si se manda, esta recomendación queda ligada a la obra — permite medir
    # después si se concretó en una cotización de ese mismo proyecto.
    proyecto_id: int | None = None


class RecomendacionKitOut(BaseModel):
    recomendacion_id: int | None
    tipo_kit: str
    confianza_tipo_kit: float
    complementos_recomendados: list[str]
    metodo_crucetas_recomendado: str | None
    zona_referencia: str | None
    n_obras_similares: int
    # Productos reales y cercanos por categoría (principal + complementos):
    # {"azulejo": [...], "pegazulejo": [...], "cruceta": [...], "emboquillado": [...]}
    materiales_recomendados: dict[str, list[ProductoCercanoOut]] = Field(
        default_factory=dict
    )


class RecomendacionesMetricasOut(BaseModel):
    total_solicitudes: int
    total_usadas: int
    tasa_uso: float
