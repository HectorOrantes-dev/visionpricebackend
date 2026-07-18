"""Router de recomendaciones (kits de instalación por zona)."""
from fastapi import APIRouter, Depends

from src.features.recomendaciones.application.entrenar_modelos import EntrenarModelos
from src.features.recomendaciones.application.recomendar_kit import RecomendarKit
from src.features.recomendaciones.domain.entities import ObraNueva
from src.features.recomendaciones.infrastructure.dependencies import (
    get_entrenar_modelos,
    get_recomendacion_uso_repository,
    get_recomendar_kit,
)
from src.features.recomendaciones.infrastructure.repository import (
    SqlAlchemyRecomendacionUsoRepository,
)
from src.features.cotizaciones.infrastructure.schemas import ProductoCercanoOut
from src.features.recomendaciones.infrastructure.schemas import (
    EntrenarOut,
    RecomendacionesMetricasOut,
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
    user: CurrentUser = Depends(cualquier_rol),
    use_case: RecomendarKit = Depends(get_recomendar_kit),
) -> RecomendacionKitOut:
    recomendacion = await use_case.recomendar(
        ObraNueva(
            lat=body.lat,
            lng=body.lng,
            categoria=body.categoria,
            area_m2=body.area_m2,
            proyecto_id=body.proyecto_id,
        ),
        k=body.k,
        usuario_id=user.id,
    )
    return RecomendacionKitOut(
        recomendacion_id=recomendacion.recomendacion_id,
        tipo_kit=recomendacion.tipo_kit,
        confianza_tipo_kit=recomendacion.confianza_tipo_kit,
        complementos_recomendados=recomendacion.complementos_recomendados,
        metodo_crucetas_recomendado=recomendacion.metodo_crucetas_recomendado,
        zona_referencia=recomendacion.zona_referencia,
        n_obras_similares=recomendacion.n_obras_similares,
        materiales_recomendados={
            categoria: [ProductoCercanoOut(**p.__dict__) for p in productos]
            for categoria, productos in recomendacion.materiales_recomendados.items()
        },
    )


@router.get(
    "/metricas",
    response_model=RecomendacionesMetricasOut,
    summary="Contador de uso: cuántas recomendaciones se pidieron vs. cuántas se concretaron en una cotización",
)
async def metricas(
    _: CurrentUser = Depends(solo_ingeniero),
    repo: SqlAlchemyRecomendacionUsoRepository = Depends(
        get_recomendacion_uso_repository
    ),
) -> RecomendacionesMetricasOut:
    total, usadas = await repo.contar_uso()
    return RecomendacionesMetricasOut(
        total_solicitudes=total,
        total_usadas=usadas,
        tasa_uso=round(usadas / total, 4) if total else 0.0,
    )
