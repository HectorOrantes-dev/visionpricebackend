"""Composición de dependencias de la feature recomendaciones.

ArbolTipoKit y KnnZona son singletons de proceso: cargan sus artefactos
.joblib una sola vez (lazy, en el primer uso) y quedan en memoria — no tiene
sentido releerlos de disco en cada request.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.cotizaciones.infrastructure.proveedores_adapter import (
    ProvidersAdapter,
)
from src.features.recomendaciones.application.entrenar_modelos import EntrenarModelos
from src.features.recomendaciones.application.recomendar_kit import RecomendarKit
from src.features.recomendaciones.domain.ports import ObrasDataset
from src.features.recomendaciones.infrastructure.dataset_combinado import (
    ObrasDatasetCombinado,
)
from src.features.recomendaciones.infrastructure.dataset_real import ObrasDatasetReal
from src.features.recomendaciones.infrastructure.dataset_sintetico import (
    ObrasDatasetSintetico,
)
from src.features.recomendaciones.infrastructure.modelos import ArbolTipoKit, KnnZona

_arbol = ArbolTipoKit()
_knn = KnnZona()


def get_dataset(
    session: AsyncSession = Depends(get_session),
) -> ObrasDataset:
    return ObrasDatasetCombinado(
        real=ObrasDatasetReal(session=session, proveedores=ProvidersAdapter()),
        sintetico=ObrasDatasetSintetico(),
    )


def get_entrenar_modelos(
    dataset: ObrasDataset = Depends(get_dataset),
) -> EntrenarModelos:
    return EntrenarModelos(dataset=dataset, arbol=_arbol, knn=_knn)


def get_recomendar_kit() -> RecomendarKit:
    return RecomendarKit(arbol=_arbol, knn=_knn)
