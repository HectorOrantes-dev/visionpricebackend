"""Puertos de la feature recomendaciones."""
from abc import ABC, abstractmethod

from src.features.recomendaciones.domain.entities import (
    MetodoCrucetas,
    Obra,
    ObraNueva,
    RecomendacionKit,
    TipoKit,
)


class ObrasDataset(ABC):
    """Acceso al histórico de obras. `cargar` es async porque el adaptador
    real consulta la BD (presupuestos/detalle_presupuesto) y al microservicio
    de Proveedores (para la categoría del producto)."""

    @abstractmethod
    async def cargar(self) -> list[Obra]:
        ...


class ClasificadorTipoKit(ABC):
    """Árbol de decisión (Gini): ¿kit o rendimiento simple?"""

    @abstractmethod
    def entrenar(self, obras: list[Obra]) -> float:
        """Entrena y devuelve el accuracy en el holdout de validación."""

    @abstractmethod
    def predecir(self, categoria: str, area_m2: float) -> tuple[TipoKit, float]:
        """Devuelve (clase predicha, probabilidad de esa clase)."""


class RecomendadorZona(ABC):
    """K-NN geográfico: ¿qué se usó en obras similares cercanas?"""

    @abstractmethod
    def entrenar(self, obras: list[Obra]) -> None:
        ...

    @abstractmethod
    def vecinos_mas_cercanos(
        self, *, lat: float, lng: float, categoria: str, k: int
    ) -> list[Obra]:
        ...


class RecomendarKitPort(ABC):
    @abstractmethod
    async def recomendar(self, obra: ObraNueva, k: int) -> RecomendacionKit:
        ...
