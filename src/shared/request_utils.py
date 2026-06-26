"""Utilidades de request HTTP compartidas."""
from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    """IP real del cliente.

    Detrás del proxy de Railway, la IP del cliente viene en X-Forwarded-For
    (el primer valor de la lista). Solo se usa para auditoría: NO se bloquea
    ni se filtra por IP.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
