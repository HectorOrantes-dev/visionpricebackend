"""Gateway al microservicio de Extracciones (audio -> JSON estructurado).

Autenticación servicio-a-servicio con header X-Api-Key (MICROSERVICE_API_KEY).
"""
import httpx

from src.core.config import settings
from src.shared.errors import UpstreamError


class ExtractionsGateway:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 60,
    ) -> None:
        self._base = (base_url or settings.extractions_base_url).rstrip("/")
        self._api_key = api_key or settings.extractions_api_key
        self._timeout = timeout

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Api-Key": self._api_key}

    def _ensure_config(self) -> None:
        if not self._base or not self._api_key:
            raise UpstreamError(
                "EXTRACTIONS_BASE_URL / EXTRACTIONS_API_KEY no configurados."
            )

    async def create_extraction(
        self, user_hash: str, filename: str, audio: bytes, content_type: str
    ) -> dict:
        self._ensure_config()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base}/extractions/",
                    headers=self._headers,
                    data={"user_hash": user_hash},
                    files={"audio": (filename, audio, content_type)},
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                "No se pudo contactar al servicio de Extracciones.",
                details={"upstream": str(exc)},
            ) from exc
        if resp.status_code >= 400:
            raise UpstreamError(
                "El servicio de Extracciones devolvió error.",
                details={"status": resp.status_code, "body": _safe(resp)},
            )
        return resp.json()

    async def submit_audio(
        self,
        *,
        grabacion_id: int,
        user_hash: str,
        proyecto_id: int | None,
        filename: str,
        audio: bytes,
        content_type: str,
    ) -> dict:
        """Envía el audio para procesamiento async.

        El microservicio guarda el audio en su object storage y procesa en
        segundo plano; al terminar llama de vuelta a /api/v1/ml/callback.
        Devuelve el ack del microservicio (idealmente con object_storage_key).
        """
        self._ensure_config()
        data = {
            "grabacion_id": str(grabacion_id),
            "user_hash": user_hash,
        }
        if proyecto_id is not None:
            data["proyecto_id"] = str(proyecto_id)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base}/extractions/",
                    headers=self._headers,
                    data=data,
                    files={"audio": (filename, audio, content_type)},
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                "No se pudo contactar al servicio de Extracciones.",
                details={"upstream": str(exc)},
            ) from exc
        if resp.status_code >= 400:
            raise UpstreamError(
                "El servicio de Extracciones devolvió error.",
                details={"status": resp.status_code, "body": _safe(resp)},
            )
        return resp.json()

    async def list_by_user(self, user_hash: str) -> dict | list:
        self._ensure_config()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self._base}/extractions/user/{user_hash}",
                    headers=self._headers,
                )
        except httpx.HTTPError as exc:
            raise UpstreamError(
                "No se pudo contactar al servicio de Extracciones.",
                details={"upstream": str(exc)},
            ) from exc
        if resp.status_code >= 400:
            raise UpstreamError(
                "El servicio de Extracciones devolvió error.",
                details={"status": resp.status_code, "body": _safe(resp)},
            )
        return resp.json()


def _safe(resp: httpx.Response):
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return resp.text
