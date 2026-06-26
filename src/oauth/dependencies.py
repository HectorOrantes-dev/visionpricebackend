"""Validación del JWT entrante y extracción del usuario actual.

Este es el lado "servidor" del JWT: cualquier ruta protegida de esta API usa
`get_current_user` para exigir y validar el `Authorization: Bearer <JWT>`.
Es el mismo token que emite la feature login y que valida el microservicio
de Pagos (HS256 con JWT_SECRET compartido).
"""
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.shared.errors import Unauthorized
from src.shared.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: int
    correo: str | None
    rol: str | None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise Unauthorized("Falta el header Authorization: Bearer <token>.")

    payload = decode_access_token(credentials.credentials)
    sub = payload.get("sub")
    if sub is None:
        raise Unauthorized("Token sin claim 'sub'.")

    try:
        user_id = int(sub)
    except (TypeError, ValueError) as exc:
        raise Unauthorized("Claim 'sub' inválido.") from exc

    return CurrentUser(
        id=user_id,
        correo=payload.get("email"),
        rol=payload.get("rol"),
    )


async def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Devuelve el JWT crudo (para reenviarlo a otros microservicios)."""
    if credentials is None or not credentials.credentials:
        raise Unauthorized("Falta el header Authorization: Bearer <token>.")
    return credentials.credentials
