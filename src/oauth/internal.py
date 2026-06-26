"""Autenticación servicio-a-servicio para webhooks ENTRANTES.

Los microservicios de ML y Pagos llaman de vuelta a esta API con el header
`X-Api-Key: <WEBHOOK_API_KEY>`. Aquí es donde se restringe ese acceso.
"""
import hmac

from fastapi import Header

from src.core.config import settings
from src.shared.errors import Unauthorized


async def require_internal_key(
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
) -> None:
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.webhook_api_key):
        raise Unauthorized("X-Api-Key inválida o ausente.")
