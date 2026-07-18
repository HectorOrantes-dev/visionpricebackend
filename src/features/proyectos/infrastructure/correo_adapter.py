"""Adaptador de correo que llama al micro 2FA.

PENDIENTE ⚠️: el micro 2FA aún no tiene el endpoint POST /correo/enviar.
Mientras tanto este adaptador falla silenciosamente (log warning) sin romper
el flujo de creación de invitaciones — el código igual se devuelve en la respuesta.

Cuando el endpoint esté disponible, solo hay que configurar TWO_FACTOR_API_KEY
en .env y el adaptador funcionará automáticamente.
"""
import logging

import httpx

from src.core.config import settings
from src.features.proyectos.domain.ports import CorreoPort

_log = logging.getLogger("proyectos.correo")


class CorreoAdapter2FA(CorreoPort):
    """Llama a POST {2FA_BASE}/correo/enviar con X-Api-Key."""

    async def enviar(self, correo: str, asunto: str, cuerpo: str) -> None:
        api_key = getattr(settings, "two_factor_api_key", "")
        if not api_key:
            _log.info(
                "two_factor_api_key no configurada — correo a %s omitido (pendiente ⚠️).",
                correo,
            )
            return

        url = f"{settings.two_factor_base_url}/correo/enviar"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    url,
                    json={"correo": correo, "asunto": asunto, "cuerpo": cuerpo},
                    headers={"X-Api-Key": api_key},
                )
                resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            _log.warning(
                "Error enviando correo de invitación a %s vía micro 2FA: %s",
                correo,
                exc,
            )
            # Falla silenciosa: el código de invitación ya fue creado.
