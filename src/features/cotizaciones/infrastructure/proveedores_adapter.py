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
        image_url=d.get("image_url") if d.get("image_url") else None,
        proveedor_id=str(prov.get("proveedor_id") or d.get("proveedor_id")) if (prov.get("proveedor_id") or d.get("proveedor_id")) else None,
        proveedor_nombre=prov.get("nombre") or d.get("proveedor_nombre"),
        proveedor_lat=float(prov["lat"]) if prov.get("lat") is not None else None,
        proveedor_lng=float(prov["lng"]) if prov.get("lng") is not None else None,
        distancia_km=(
            float(prov["distancia_km"]) if prov.get("distancia_km") is not None else None
        ),
        pieza_largo_m=_f("pieza_largo_m"),
        pieza_ancho_m=_f("pieza_ancho_m"),
        piezas_por_paquete=(
            int(d["piezas_por_paquete"])
            if d.get("piezas_por_paquete") is not None
            else None
        ),
    )


# Los proveedores todavía no usan estas categorías como algo distinto de la
# categoría "padre" — todo azulejo/mosaico de pared lo cargan bajo "piso".
# Mientras el catálogo no lo separe, si la categoría pedida no trae productos
# se reintenta con su categoría "padre" en vez de devolver vacío. Quitar la
# entrada de este mapa el día que los proveedores empiecen a etiquetar bien.
_FALLBACK_CATEGORIA = {
    "azulejo": "piso",
}


class ProvidersAdapter(ProveedoresPort):
    def __init__(self, gateway: ProvidersGateway | None = None) -> None:
        self._gateway = gateway or ProvidersGateway()

    async def productos_cercanos(
        self, *, lat, lng, radio_km, categoria=None
    ) -> list[ProductoCercano]:
        data = await self._gateway.productos_cercanos(
            lat=lat, lng=lng, radio_km=radio_km, categoria=categoria
        )
        if not data and categoria:
            fallback = _FALLBACK_CATEGORIA.get(categoria.lower().strip())
            if fallback:
                data = await self._gateway.productos_cercanos(
                    lat=lat, lng=lng, radio_km=radio_km, categoria=fallback
                )
        return [_to_producto(d) for d in data]

    async def productos_por_ids(self, ids: list[str]) -> list[ProductoCercano]:
        data = await self._gateway.productos_por_ids(ids)
        return [_to_producto(d) for d in data]
