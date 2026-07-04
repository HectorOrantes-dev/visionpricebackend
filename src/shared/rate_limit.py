"""Rate limiting simple en memoria — mitiga el polling excesivo del cliente.

Ventana deslizante por (usuario + ruta concreta). Es por instancia (en memoria);
suficiente para frenar un sondeo desbocado del móvil. Para multi-instancia se
necesitaría un backend compartido (Redis).

Uso en una ruta:
    user: CurrentUser = Depends(rate_limit(20, 30))   # 20 req / 30 s
"""
import time
from collections import defaultdict, deque

from fastapi import Depends, Request

from src.oauth.dependencies import CurrentUser, get_current_user
from src.shared.errors import TooManyRequests

_buckets: dict[str, deque] = defaultdict(deque)


def rate_limit(max_requests: int, window_seconds: int):
    async def _dep(
        request: Request,
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        key = f"{user.id}:{request.scope['path']}"
        ahora = time.monotonic()
        limite = ahora - window_seconds
        dq = _buckets[key]
        while dq and dq[0] < limite:
            dq.popleft()
        if len(dq) >= max_requests:
            raise TooManyRequests(
                "Demasiadas peticiones seguidas al mismo recurso. "
                "Espera unos segundos.",
                details={"max": max_requests, "ventana_segundos": window_seconds},
            )
        dq.append(ahora)
        return user

    return _dep
