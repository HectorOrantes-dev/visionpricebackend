"""Rutas protegidas de ejemplo: identidad del usuario y proxy a Pagos.

Demuestra cómo el resto de features deben:
  - exigir el JWT con `get_current_user`,
  - reenviar el token a otros microservicios con `get_bearer_token`.
"""
from fastapi import APIRouter, Depends

from src.microservices.payments_gateway import PaymentsGateway
from src.oauth.dependencies import CurrentUser, get_bearer_token, get_current_user

router = APIRouter(tags=["account"])


@router.get("/me", summary="Identidad del usuario autenticado (desde el JWT)")
async def me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {"id": user.id, "correo": user.correo, "rol": user.rol}


@router.get(
    "/me/subscriptions",
    summary="Historial de suscripciones (proxy al microservicio de Pagos)",
)
async def my_subscriptions(
    _: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_bearer_token),
) -> dict | list:
    return await PaymentsGateway().list_subscriptions(token)
