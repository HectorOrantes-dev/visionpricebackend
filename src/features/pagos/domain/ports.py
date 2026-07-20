"""Puerto de entitlement: lo único de Pagos que cachea la API principal."""
from abc import ABC, abstractmethod
from datetime import datetime


class EntitlementRepository(ABC):
    @abstractmethod
    async def leer_plan(self, usuario_id: int) -> str | None:
        """Plan activo actual del usuario (None si no tiene / no existe).

        Se lee ANTES de actualizar para decidir si la suscripción se acaba de
        activar o cambió de plan, y notificar solo entonces (no en cada sync).
        """

    @abstractmethod
    async def actualizar(
        self,
        usuario_id: int,
        plan_activo: str | None,
        vigencia_hasta: datetime | None,
    ) -> bool:
        """Actualiza plan/vigencia del usuario. Devuelve False si no existe."""
