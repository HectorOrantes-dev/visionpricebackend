"""Puerto del repositorio de auditoría de precios."""
from abc import ABC, abstractmethod

from src.features.auditoria_precios.domain.entities import LineaPrecio


class AuditoriaRepository(ABC):
    @abstractmethod
    async def coords_de_presupuesto(
        self, presupuesto_id: int
    ) -> tuple[float | None, float | None] | None:
        """(lat, lng) del proyecto del presupuesto; None si no existe."""

    @abstractmethod
    async def lineas_de_presupuesto(self, presupuesto_id: int) -> list[LineaPrecio]:
        ...

    @abstractmethod
    async def historico_precios(
        self,
        material_id: str,
        *,
        lat: float | None,
        lng: float | None,
        precision: int,
        excluir_presupuesto: int | None = None,
    ) -> list[float]:
        """Precios históricos de ese material en la zona (rejilla lat/lng)."""

    @abstractmethod
    async def lineas_en_zona(
        self, *, lat: float, lng: float, precision: int
    ) -> list[LineaPrecio]:
        ...
