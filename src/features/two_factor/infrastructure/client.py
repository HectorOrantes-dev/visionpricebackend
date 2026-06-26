"""Adaptador HTTP al microservicio 2FA de VisionPrice.

Implementa `TwoFactorPort` llamando a:
  - POST {base}/2fa/send    -> genera + envía el correo
  - POST {base}/2fa/verify  -> { valid, reason }
"""
import httpx

from src.core.config import settings
from src.features.two_factor.domain.ports import TwoFactorPort, TwoFactorResult
from src.shared.errors import UpstreamError


class HttpTwoFactorClient(TwoFactorPort):
    def __init__(
        self, base_url: str | None = None, timeout: int | None = None
    ) -> None:
        self._base = (base_url or settings.two_factor_base_url).rstrip("/")
        self._timeout = timeout or settings.two_factor_timeout

    async def send_code(self, email: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base}/2fa/send", json={"email": email}
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                "No se pudo contactar al servicio 2FA.", details={"upstream": str(exc)}
            ) from exc

        if resp.status_code >= 400:
            raise UpstreamError(
                "El servicio 2FA no pudo enviar el código.",
                details={"status": resp.status_code, "body": _safe_json(resp)},
            )

    async def verify_code(self, email: str, code: str) -> TwoFactorResult:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base}/2fa/verify",
                    json={"email": email, "code": code},
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                "No se pudo contactar al servicio 2FA.", details={"upstream": str(exc)}
            ) from exc

        if resp.status_code >= 400:
            raise UpstreamError(
                "El servicio 2FA devolvió un error al verificar.",
                details={"status": resp.status_code, "body": _safe_json(resp)},
            )

        data = resp.json()
        return TwoFactorResult(
            valid=bool(data.get("valid")),
            reason=str(data.get("reason", "")),
        )


def _safe_json(resp: httpx.Response):
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return resp.text
