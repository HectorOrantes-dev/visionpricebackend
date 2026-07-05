"""Gateway al microservicio de Extracciones (audio -> JSON estructurado).

Autenticación servicio-a-servicio con header X-Api-Key (MICROSERVICE_API_KEY).
Reintenta ante fallos transitorios del micro (502/503/504, conexión).
"""
import asyncio
import logging

import httpx

from src.core.config import settings
from src.shared.errors import UpstreamError

_log = logging.getLogger("extractions.gateway")

# Estados HTTP que suelen ser transitorios (micro reiniciando / saturado).
_TRANSITORIOS = {502, 503, 504}


class ExtractionsGateway:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
        max_reintentos: int | None = None,
    ) -> None:
        self._base = (base_url or settings.extractions_base_url).rstrip("/")
        self._api_key = api_key or settings.extractions_api_key
        self._timeout = timeout or settings.extractions_timeout
        self._max_reintentos = (
            max_reintentos
            if max_reintentos is not None
            else settings.extractions_max_reintentos
        )

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
        # Contrato exacto del micro: grabacion_id, proyecto_id, audio (multipart).
        # (user_hash es legado del micro anterior; ya no se envía.)
        data = {"grabacion_id": str(grabacion_id)}
        if proyecto_id is not None:
            data["proyecto_id"] = str(proyecto_id)

        ultimo_error: UpstreamError | None = None
        for intento in range(self._max_reintentos + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        f"{self._base}/extractions/",
                        headers=self._headers,
                        data=data,
                        files={"audio": (filename, audio, content_type)},
                    )
            except httpx.HTTPError as exc:
                ultimo_error = UpstreamError(
                    "No se pudo contactar al servicio de Extracciones.",
                    details={"upstream": str(exc)},
                )
            else:
                if resp.status_code < 400:
                    return resp.json()
                ultimo_error = UpstreamError(
                    "El servicio de Extracciones devolvió error.",
                    details={"status": resp.status_code, "body": _safe(resp)},
                )
                # Solo reintenta fallos transitorios; 4xx (mal request) no.
                if resp.status_code not in _TRANSITORIOS:
                    raise ultimo_error

            if intento < self._max_reintentos:
                espera = 2 ** intento  # backoff: 1s, 2s, 4s...
                _log.warning(
                    "Extracciones falló (intento %s/%s), reintentando en %ss...",
                    intento + 1,
                    self._max_reintentos + 1,
                    espera,
                )
                await asyncio.sleep(espera)

        raise ultimo_error  # se agotaron los reintentos

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
