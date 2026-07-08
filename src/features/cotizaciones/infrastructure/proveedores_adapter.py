"""Adaptador del puerto ProveedoresPort sobre el ProvidersGateway.

Traduce los dicts del micro de Proveedores a entidades ProductoCercano. Si tu
micro usa nombres de campo distintos, ajústalos aquí (único punto de mapeo).
"""
from src.features.cotizaciones.domain.entities import ProductoCercano
from src.features.cotizaciones.domain.ports import ProveedoresPort
from src.microservices.providers_gateway import ProvidersGateway


def _to_producto(d: dict) -> ProductoCercano:
    prov = d.get("proveedor") or {}
    def _f(key: str) -> float | None:
        return float(d[key]) if d.get(key) is not None else None

    return ProductoCercano(
        producto_id=str(d.get("producto_id") or d.get("id")),
        nombre=d.get("nombre", ""),
        categoria=d.get("categoria", ""),
        unidad=d.get("unidad", "pieza"),
        precio_unitario=float(d.get("precio_unitario", 0) or 0),
        rendimiento_m2=_f("rendimiento_m2"),
        image_url=d.get("image_url"),
        proveedor_id=str(prov.get("proveedor_id") or d.get("proveedor_id")) if (prov.get("proveedor_id") or d.get("proveedor_id")) else None,
        proveedor_nombre=prov.get("nombre") or d.get("proveedor_nombre"),
        proveedor_lat=float(prov["lat"]) if prov.get("lat") is not None else None,
        proveedor_lng=float(prov["lng"]) if prov.get("lng") is not None else None,
        distancia_km=(
            float(prov["distancia_km"]) if prov.get("distancia_km") is not None else None
        ),
    )


class ProvidersAdapter(ProveedoresPort):
    def __init__(self, gateway: ProvidersGateway | None = None) -> None:
        self._gateway = gateway or ProvidersGateway()

    async def productos_cercanos(
        self, *, lat, lng, radio_km, categoria=None
    ) -> list[ProductoCercano]:
        data = await self._gateway.productos_cercanos(
            lat=lat, lng=lng, radio_km=radio_km, categoria=categoria
        )
        return [_to_producto(d) for d in data]

    async def productos_por_ids(self, ids: list[int]) -> list[ProductoCercano]:
        data = await self._gateway.productos_por_ids(ids)
        return [_to_producto(d) for d in data]
