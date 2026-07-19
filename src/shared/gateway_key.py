"""Middleware de validación del API Gateway (fase de rollout OPCIONAL).

Reusable: móntalo con app.add_middleware(GatewayKeyMiddleware).

Comportamiento actual (dual-accept, para no romper producción mientras el
móvil todavía le pega directo a esta API en vez de al gateway):
  - settings.gateway_shared_key vacío  -> no-op total (como hoy).
  - Header X-Gateway-Key AUSENTE       -> deja pasar igual (fase de rollout).
  - Header X-Gateway-Key PRESENTE pero incorrecto -> 401, corta acá.
  - Header X-Gateway-Key PRESENTE y correcto       -> pasa.

Cuando el móvil ya solo le pegue al gateway, cambiar la rama "ausente" para
que también rechace (comparar contra None además de contra el valor) — ese
es el modo estricto, un cambio de una línea acá cuando se confirme el
cutover completo.
"""
import hmac
import json

from src.core.config import settings

_EXCLUIDOS = ("/health",)


class GatewayKeyMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not settings.gateway_shared_key:
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if path in _EXCLUIDOS:
            return await self.app(scope, receive, send)

        recibida = _header(scope, b"x-gateway-key")
        if recibida is not None and not hmac.compare_digest(
            recibida.decode(), settings.gateway_shared_key
        ):
            return await _rechazar(send)

        return await self.app(scope, receive, send)


def _header(scope, nombre: bytes) -> bytes | None:
    for k, v in scope["headers"]:
        if k == nombre:
            return v
    return None


async def _rechazar(send) -> None:
    body = json.dumps(
        {"error": {"code": "unauthorized", "message": "X-Gateway-Key inválida."}}
    ).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 401,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})
