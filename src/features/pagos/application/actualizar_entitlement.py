"""Caso de uso: actualizar el entitlement cacheado desde el micro de Pagos.

La fuente de verdad de la facturación es el microservicio de Pagos. Aquí sólo
guardamos un resumen ligero (plan + vigencia) para autorizar rápido sin
depender de que Pagos responda en cada request.
"""
from dataclasses import dataclass
from datetime import datetime

from src.features.pagos.domain.ports import EntitlementRepository
from src.shared.errors import NotFound
from src.shared.timeutils import to_naive_utc

# Estados de suscripción que conceden acceso.
ESTADOS_ACTIVOS = {"active", "trialing", "pending"}


@dataclass
class EntitlementCommand:
    user_id: int
    plan_key: str
    status: str
    current_period_end: datetime | None


class ActualizarEntitlement:
    def __init__(self, repo: EntitlementRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: EntitlementCommand) -> None:
        activo = cmd.status in ESTADOS_ACTIVOS
        plan = cmd.plan_key if activo else None
        # Normaliza a UTC naive (la fecha llega con tz desde el ISO con 'Z').
        vigencia = to_naive_utc(cmd.current_period_end) if activo else None

        actualizado = await self._repo.actualizar(cmd.user_id, plan, vigencia)
        if not actualizado:
            raise NotFound(f"Usuario {cmd.user_id} no encontrado.")
