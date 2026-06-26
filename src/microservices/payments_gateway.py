"""Gateway al microservicio de Pagos.

El microservicio valida el MISMO JWT que emite esta API, así que aquí sólo
reenviamos el token del usuario en el header Authorization.
"""
import httpx

from src.core.config import settings
from src.shared.errors import UpstreamError


class PaymentsGateway:
    def __init__(self, base_url: str | None = None, timeout: int = 20) -> None:
        self._base = (base_url or settings.payments_base_url).rstrip("/")
        self._timeout = timeout

    async def _get(self, path: str, jwt: str) -> dict | list:
        if not self._base:
            raise UpstreamError("PAYMENTS_BASE_URL no está configurado.")
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base}{path}",
                    headers={"Authorization": f"Bearer {jwt}"},
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                "No se pudo contactar al servicio de Pagos.",
                details={"upstream": str(exc)},
            ) from exc
        if resp.status_code >= 400:
            raise UpstreamError(
                "El servicio de Pagos devolvió error.",
                details={"status": resp.status_code, "body": _safe(resp)},
            )
        return resp.json()

    async def list_subscriptions(self, jwt: str) -> dict | list:
        return await self._get("/subscriptions", jwt)

    async def active_subscriptions(self, jwt: str) -> dict | list:
        return await self._get("/subscriptions/active", jwt)


def _safe(resp: httpx.Response):
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return resp.text
