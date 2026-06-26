"""Primitivas de seguridad: hashing de contraseñas y emisión/validación de JWT.

El JWT se firma con HS256 usando JWT_SECRET — el MISMO secreto que valida el
microservicio de Pagos. El claim `sub` lleva el id del usuario.
"""
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from src.core.config import settings
from src.shared.errors import Unauthorized

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(
    *, user_id: int, email: str, rol: str | None = None
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "rol": rol,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise Unauthorized("El token ha expirado.") from exc
    except jwt.PyJWTError as exc:
        raise Unauthorized("Token inválido.") from exc
