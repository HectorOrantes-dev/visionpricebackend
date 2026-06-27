"""Gateway al microservicio de Proveedores.

Autenticación servicio-a-servicio con X-Api-Key. La API principal solo reenvía
lat/lng (la ubicación que manda la app); el micro hace el mapeo geográfico y
devuelve los productos de proveedores cercanos. Devuelve dicts crudos; el
adaptador de la feature los traduce a entidades de dominio.
"""
import httpx

from src.core.config import settings
from src.shared.errors import UpstreamError


class ProvidersGateway:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 20,
    ) -> None:
        self._base = (base_url or settings.providers_base_url).rstrip("/")
        self._api_key = api_key or settings.providers_api_key
        self._timeout = timeout

    def _ensure_config(self) -> None:
        if not self._base or not self._api_key:
            raise UpstreamError(
                "PROVIDERS_BASE_URL / PROVIDERS_API_KEY no configurados."
            )

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Api-Key": self._api_key}

    async def _get(self, path: str, params: dict) -> list[dict]:
        self._ensure_config()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base}{path}", params=params, headers=self._headers
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                "No se pudo contactar al servicio de Proveedores.",
                details={"upstream": str(exc)},
            ) from exc
        if resp.status_code >= 400:
            raise UpstreamError(
                "El servicio de Proveedores devolvió error.",
                details={"status": resp.status_code, "body": _safe(resp)},
            )
        data = resp.json()
        # Acepta tanto una lista como {"productos": [...]} / {"items": [...]}.
        if isinstance(data, dict):
            data = data.get("productos") or data.get("items") or []
        return data

    async def productos_cercanos(
        self,
        *,
        lat: float,
        lng: float,
        radio_km: float,
        categoria: str | None = None,
    ) -> list[dict]:
        params = {"lat": lat, "lng": lng, "radio_km": radio_km}
        if categoria:
            params["categoria"] = categoria
        return await self._get("/productos/cercanos", params)

    async def productos_por_ids(self, ids: list[int]) -> list[dict]:
        if not ids:
            return []
        return await self._get(
            "/productos", {"ids": ",".join(str(i) for i in ids)}
        )


def _safe(resp: httpx.Response):
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return resp.text
