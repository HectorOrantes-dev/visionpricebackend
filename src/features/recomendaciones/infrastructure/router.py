"""Router de recomendaciones (kits de instalación por zona)."""
from fastapi import APIRouter, Depends

from src.features.recomendaciones.application.entrenar_modelos import EntrenarModelos
from src.features.recomendaciones.application.recomendar_kit import RecomendarKit
from src.features.recomendaciones.domain.entities import ObraNueva
from src.features.recomendaciones.infrastructure.dependencies import (
    get_entrenar_modelos,
    get_recomendar_kit,
)
from src.features.recomendaciones.infrastructure.schemas import (
    EntrenarOut,
    RecomendacionKitOut,
    RecomendarKitRequest,
)
from src.oauth.dependencies import CurrentUser
from src.oauth.permisos import Permisos
from src.oauth.roles import require_roles

router = APIRouter(prefix="/recomendaciones", tags=["recomendaciones"])

solo_ingeniero = require_roles(*Permisos.ENTRENAR_MODELOS)
cualquier_rol = require_roles(*Permisos.RECOMENDACIONES)


@router.post(
    "/entrenar",
    response_model=EntrenarOut,
    summary="(Re)entrenar el árbol de tipo de kit y el K-NN de zona sobre el dataset actual",
)
async def entrenar(
    _: CurrentUser = Depends(solo_ingeniero),
    use_case: EntrenarModelos = Depends(get_entrenar_modelos),
) -> EntrenarOut:
    metricas = await use_case.execute()
    return EntrenarOut(**metricas.__dict__)


@router.post(
    "/kit",
    response_model=RecomendacionKitOut,
    summary="Recomendar tipo de kit, complementos y método de junta para una obra nueva",
)
async def recomendar(
    body: RecomendarKitRequest,
    _: CurrentUser = Depends(cualquier_rol),
    use_case: RecomendarKit = Depends(get_recomendar_kit),
) -> RecomendacionKitOut:
    recomendacion = await use_case.recomendar(
        ObraNueva(
            lat=body.lat,
            lng=body.lng,
            categoria=body.categoria,
            area_m2=body.area_m2,
        ),
        k=body.k,
    )
    return RecomendacionKitOut(**recomendacion.__dict__)
