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
    async def recomendar(
        self, obra: ObraNueva, k: int, *, usuario_id: int
    ) -> RecomendacionKit:
        ...


class RecomendacionUsoRepository(ABC):
    """Auditoría: qué se recomendó y si se terminó usando en una cotización."""

    @abstractmethod
    async def registrar_solicitud(
        self,
        *,
        usuario_id: int,
        proyecto_id: int | None,
        recomendacion: RecomendacionKit,
        categoria: str,
    ) -> int:
        """Persiste la recomendación devuelta al cliente y devuelve su id."""

    @abstractmethod
    async def marcar_usada(self, recomendacion_id: int, cotizacion_id: int) -> bool:
        """True si existía y se marcó; False si el id no existe."""

    @abstractmethod
    async def contar_uso(self) -> tuple[int, int]:
        """(total_solicitudes, total_usadas)."""
