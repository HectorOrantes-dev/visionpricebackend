"""Caso de uso: listar productos de proveedores cercanos a una ubicación."""
from dataclasses import dataclass

from src.features.cotizaciones.domain.entities import ProductoCercano
from src.features.cotizaciones.domain.ports import ProveedoresPort


@dataclass
class ProductosCercanosQuery:
    lat: float
    lng: float
    radio_km: float
    categoria: str | None = None


class ListarProductosCercanos:
    def __init__(self, proveedores: ProveedoresPort) -> None:
        self._proveedores = proveedores

    async def execute(
        self, query: ProductosCercanosQuery
    ) -> list[ProductoCercano]:
        return await self._proveedores.productos_cercanos(
            lat=query.lat,
            lng=query.lng,
            radio_km=query.radio_km,
            categoria=query.categoria,
        )
