"""Verificador del id_token de Google con PyJWT + JWKS.

Valida firma (RS256 contra las claves públicas de Google), `aud` (uno de tus
client IDs), `iss` y expiración. No requiere llamar a Google en cada login:
PyJWKClient cachea las claves.
"""
import jwt
from jwt import PyJWKClient

from src.features.google_auth.domain.entities import GoogleIdentity
from src.features.google_auth.domain.ports import GoogleIdentityVerifier
from src.shared.errors import Unauthorized

_GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_VALID_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}

# Cliente JWKS compartido. En producción cachea las claves públicas de Google
# (no se llama a Google en cada login); se refrescan cada hora.
_jwks_client = PyJWKClient(
    _GOOGLE_CERTS_URL,
    cache_keys=True,
    max_cached_keys=16,
    cache_jwk_set=True,
    lifespan=3600,
)


class PyJwtGoogleVerifier(GoogleIdentityVerifier):
    def __init__(self, audiences: list[str]) -> None:
        self._audiences = audiences

    def verify(self, id_token: str) -> GoogleIdentity:
        if not self._audiences:
            raise Unauthorized("GOOGLE_CLIENT_IDS no está configurado.")
        try:
            signing_key = _jwks_client.get_signing_key_from_jwt(id_token)
            payload = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audiences,
                options={"require": ["exp", "aud", "iss", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise Unauthorized("id_token de Google inválido.") from exc

        if payload.get("iss") not in _VALID_ISSUERS:
            raise Unauthorized("Emisor del id_token no es Google.")

        email = payload.get("email")
        if not email:
            raise Unauthorized("El id_token no incluye email.")

        nombre = payload.get("name") or email.split("@")[0]
        return GoogleIdentity(
            sub=payload["sub"],
            email=email,
            nombre=nombre,
            email_verified=bool(payload.get("email_verified", False)),
        )
