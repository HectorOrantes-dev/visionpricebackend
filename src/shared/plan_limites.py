"""Límites de uso del plan gratuito (freemium).

La fuente de verdad de facturación es el microservicio de Pagos. Este
backend solo cachea el entitlement en `Usuario.plan_activo`/`vigencia_hasta`
(actualizado por webhook — ver
src/features/pagos/application/actualizar_entitlement.py) y lo usa acá para
gatear features.

Reglas de negocio (definidas junto al usuario):
  - 20 cotizaciones gratis de por vida por usuario (no se renuevan cada mes),
    aplican por igual a los 4 roles.
  - El método de audio (grabaciones) no tiene cuota gratis: requiere
    suscripción activa siempre, se bloquea apenas vence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.oauth.dependencies import CurrentUser, get_current_user
from src.shared.errors import PlanLimiteAlcanzado, PlanRequerido
from src.shared.models import Presupuesto, Usuario

LIMITE_COTIZACIONES_GRATIS = 20


def _plan_vigente(usuario: Usuario) -> bool:
    if not usuario.plan_activo:
        return False
    if usuario.vigencia_hasta is None:
        return True
    return usuario.vigencia_hasta > datetime.utcnow()


async def _cargar_usuario(session: AsyncSession, user_id: int) -> Usuario:
    usuario = await session.get(Usuario, user_id)
    if usuario is None:
        # No debería pasar (el JWT ya validó que el usuario existe al
        # loguearse), pero si pasa, tratarlo como sin plan es lo seguro.
        raise PlanRequerido("Usuario no encontrado.")
    return usuario


async def _contar_cotizaciones(session: AsyncSession, user_id: int) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(Presupuesto)
        .where(Presupuesto.usuario_id == user_id)
    )
    return total or 0


async def verificar_limite_cotizaciones(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """Dependencia para las rutas que CREAN una cotización (presupuesto).

    Con plan pagado y vigente, pasa sin más. Sin plan, cuenta las
    cotizaciones históricas del usuario; a partir de la 21 corta con 402.
    """
    usuario = await _cargar_usuario(session, user.id)
    if _plan_vigente(usuario):
        return user

    usadas = await _contar_cotizaciones(session, user.id)
    if usadas >= LIMITE_COTIZACIONES_GRATIS:
        raise PlanLimiteAlcanzado(
            f"Alcanzaste el límite de {LIMITE_COTIZACIONES_GRATIS} "
            "cotizaciones del plan gratuito. Actualiza tu plan para seguir "
            "generando PDFs.",
            details={"limite": LIMITE_COTIZACIONES_GRATIS, "usadas": usadas},
        )
    return user


async def requerir_plan_activo(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """Dependencia para features 100% de pago (sin cuota gratis): audio."""
    usuario = await _cargar_usuario(session, user.id)
    if not _plan_vigente(usuario):
        raise PlanRequerido(
            "Esta función requiere una suscripción activa. "
            "Actualiza tu plan para usar el método de audio."
        )
    return user


@dataclass(frozen=True)
class UsoCotizaciones:
    plan_activo: str | None
    ilimitado: bool
    limite_gratis: int
    usadas: int
    restantes: int | None  # None cuando `ilimitado` es True


async def obtener_uso_cotizaciones(
    session: AsyncSession, user_id: int
) -> UsoCotizaciones:
    usuario = await _cargar_usuario(session, user_id)
    ilimitado = _plan_vigente(usuario)
    usadas = await _contar_cotizaciones(session, user_id)
    restantes = None if ilimitado else max(LIMITE_COTIZACIONES_GRATIS - usadas, 0)
    return UsoCotizaciones(
        plan_activo=usuario.plan_activo,
        ilimitado=ilimitado,
        limite_gratis=LIMITE_COTIZACIONES_GRATIS,
        usadas=usadas,
        restantes=restantes,
    )
