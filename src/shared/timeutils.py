"""Utilidades de fecha/hora.

`utcnow()` devuelve el UTC actual SIN tzinfo (naive). Las columnas del modelo
son `TIMESTAMP` (sin zona); PostgreSQL/asyncpg rechaza datetimes con tz contra
esas columnas ("can't subtract offset-naive and offset-aware datetimes").
Usamos esto en todo lo que se escribe/compara contra la BD.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt: datetime | None) -> datetime | None:
    """Normaliza un datetime (posiblemente con tz) a UTC sin tzinfo.

    Útil para fechas que llegan de fuera (p. ej. ISO con 'Z' parseado por
    Pydantic) antes de guardarlas en columnas TIMESTAMP.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
