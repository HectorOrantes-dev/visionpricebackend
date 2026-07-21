"""Rutas protegidas de ejemplo: identidad del usuario y proxy a Pagos.

Demuestra cómo el resto de features deben:
  - exigir el JWT con `get_current_user`,
  - reenviar el token a otros microservicios con `get_bearer_token`.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.features.account.infrastructure.repository import (
    actualizar_perfil,
    obtener_perfil,
)
from src.features.account.infrastructure.schemas import (
    ActualizarPerfilRequest,
    PerfilOut,
)
from src.microservices.payments_gateway import PaymentsGateway
from src.oauth.dependencies import CurrentUser, get_bearer_token, get_current_user
from src.shared.errors import NotFound

router = APIRouter(tags=["account"])


@router.get("/me", summary="Identidad del usuario autenticado (desde el JWT)")
async def me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {"id": user.id, "correo": user.correo, "rol": user.rol}


@router.get(
    "/me/perfil",
    response_model=PerfilOut,
    summary="Perfil completo del usuario (desde la base de datos)",
)
async def mi_perfil(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PerfilOut:
    perfil = await obtener_perfil(session, user.id)
    if perfil is None:
        raise NotFound("Usuario no encontrado.")
    return PerfilOut(**perfil.__dict__)


@router.patch(
    "/me/perfil",
    response_model=PerfilOut,
    summary="Completa/actualiza nombre y/o teléfono del perfil",
)
async def actualizar_mi_perfil(
    body: ActualizarPerfilRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PerfilOut:
    perfil = await actualizar_perfil(
        session, user.id, nombre=body.nombre, telefono=body.telefono
    )
    if perfil is None:
        raise NotFound("Usuario no encontrado.")
    return PerfilOut(**perfil.__dict__)


@router.get(
    "/me/subscriptions",
    summary="Historial de suscripciones (proxy al microservicio de Pagos)",
)
async def my_subscriptions(
    _: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_bearer_token),
) -> dict | list:
    return await PaymentsGateway().list_subscriptions(token)
