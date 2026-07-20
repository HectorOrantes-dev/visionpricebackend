"""Caso de uso: actualizar el entitlement cacheado desde el micro de Pagos.

La fuente de verdad de la facturación es el microservicio de Pagos. Aquí sólo
guardamos un resumen ligero (plan + vigencia) para autorizar rápido sin
depender de que Pagos responda en cada request.
"""
import logging
from dataclasses import dataclass
from datetime import datetime

from src.features.notificaciones.application.emitir_evento import (
    EmitirEvento,
    EventoCommand,
)
from src.features.notificaciones.domain.entities import TipoNotificacion
from src.features.pagos.domain.ports import EntitlementRepository
from src.shared.errors import NotFound
from src.shared.timeutils import to_naive_utc

_log = logging.getLogger("pagos.notificar")

# Estados de suscripción que conceden acceso.
ESTADOS_ACTIVOS = {"active", "trialing", "pending"}


@dataclass
class EntitlementCommand:
    user_id: int
    plan_key: str
    status: str
    current_period_end: datetime | None


class ActualizarEntitlement:
    def __init__(
        self, repo: EntitlementRepository, emitir: EmitirEvento | None = None
    ) -> None:
        self._repo = repo
        self._emitir = emitir

    async def execute(self, cmd: EntitlementCommand) -> None:
        activo = cmd.status in ESTADOS_ACTIVOS
        plan = cmd.plan_key if activo else None
        # Normaliza a UTC naive (la fecha llega con tz desde el ISO con 'Z').
        vigencia = to_naive_utc(cmd.current_period_end) if activo else None

        # Plan previo, para notificar solo cuando pasa a activo por primera vez
        # o cambia de plan (no en cada sync repetido del mismo estado).
        plan_previo = await self._repo.leer_plan(cmd.user_id)

        actualizado = await self._repo.actualizar(cmd.user_id, plan, vigencia)
        if not actualizado:
            raise NotFound(f"Usuario {cmd.user_id} no encontrado.")

        if activo and plan != plan_previo:
            await self._notificar_activada(cmd.user_id)

    async def _notificar_activada(self, user_id: int) -> None:
        if self._emitir is None:
            return
        # Best-effort: el push no debe tumbar el webhook de pagos.
        try:
            await self._emitir.execute(
                EventoCommand(
                    usuario_id=user_id,
                    tipo=TipoNotificacion.SUSCRIPCION_ACTIVADA,
                    referencia_tipo="suscripcion",
                    referencia_id=user_id,
                )
            )
        except Exception as exc:  # noqa: BLE001
            _log.warning(
                "No se pudo emitir suscripcion_activada para usuario %s: %s",
                user_id,
                exc,
            )
