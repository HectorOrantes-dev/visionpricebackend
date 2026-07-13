"""Puertos de la feature cotizaciones."""
from abc import ABC, abstractmethod

from src.features.cotizaciones.domain.entities import (
    Cotizacion,
    LineaCotizacion,
    ProductoCercano,
    InfoProyectoPdf,
)


class ProveedoresPort(ABC):
    """Acceso al microservicio de Proveedores (catálogo + cercanía)."""

    @abstractmethod
    async def productos_cercanos(
        self,
        *,
        lat: float,
        lng: float,
        radio_km: float,
        categoria: str | None = None,
    ) -> list[ProductoCercano]:
        ...

    @abstractmethod
    async def productos_por_ids(self, ids: list[str]) -> list[ProductoCercano]:
        ...


class CotizacionRepository(ABC):
    @abstractmethod
    async def texto_transcripcion(self, grabacion_id: int) -> str | None:
        """Texto de la transcripción asociada a una grabación (o None)."""

    @abstractmethod
    async def crear(
        self,
        *,
        proyecto_id: int,
        usuario_id: int,
        total: float,
        lineas: list[LineaCotizacion],
    ) -> Cotizacion:
        ...

    @abstractmethod
    async def obtener(
        self, cotizacion_id: int, usuario_id: int
    ) -> Cotizacion | None:
        ...

    @abstractmethod
    async def listar_cotizaciones_de_proyecto(
        self, proyecto_id: int, usuario_id: int
    ) -> list[Cotizacion]:
        ...

    @abstractmethod
    async def obtener_info_proyecto(
        self, proyecto_id: int, usuario_id: int
    ) -> InfoProyectoPdf | None:
        ...


class PdfRenderer(ABC):
    @abstractmethod
    def render(self, cotizacion: Cotizacion, *, proyecto: str | None = None) -> bytes:
        ...

    @abstractmethod
    def render_proyecto(self, cotizaciones: list[Cotizacion], proyecto_id: int, info_proyecto: InfoProyectoPdf | None = None) -> bytes:
        ...
