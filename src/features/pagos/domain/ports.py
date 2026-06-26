"""Puerto de entitlement: lo único de Pagos que cachea la API principal."""
from abc import ABC, abstractmethod
from datetime import datetime


class EntitlementRepository(ABC):
    @abstractmethod
    async def actualizar(
        self,
        usuario_id: int,
        plan_activo: str | None,
        vigencia_hasta: datetime | None,
    ) -> bool:
        """Actualiza plan/vigencia del usuario. Devuelve False si no existe."""
