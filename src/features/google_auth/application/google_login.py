"""Caso de uso: login con Google.

Verifica el id_token; si el correo ya tiene cuenta, emite el JWT (y vincula el
google_sub si faltaba). Si NO existe, lanza un error específico para que el
front muestre el selector de roles y mande al register.
"""
from dataclasses import dataclass

from src.features.google_auth.domain.ports import (
    GoogleIdentityVerifier,
    GoogleUserRepository,
)
from src.shared.errors import NotFound, Unauthorized
from src.shared.security import create_access_token


@dataclass
class GoogleLoginCommand:
    id_token: str


@dataclass
class AuthToken:
    access_token: str
    token_type: str
    user_id: int
    correo: str
    rol: str
    es_nuevo: bool = False


class GoogleLogin:
    def __init__(
        self, verifier: GoogleIdentityVerifier, repo: GoogleUserRepository
    ) -> None:
        self._verifier = verifier
        self._repo = repo

    async def execute(self, cmd: GoogleLoginCommand) -> AuthToken:
        identity = self._verifier.verify(cmd.id_token)

        user = await self._repo.get_by_correo(identity.email)
        if user is None:
            raise NotFound(
                "No existe una cuenta con ese correo de Google. Regístrate.",
                details={"code_hint": "google_user_not_registered"},
            )
        if not user.activo:
            raise Unauthorized("La cuenta está desactivada.")

        if user.google_sub is None:
            await self._repo.vincular_google(user.id, identity.sub)

        token = create_access_token(
            user_id=user.id, email=user.correo, rol=user.rol
        )
        return AuthToken(
            access_token=token,
            token_type="bearer",
            user_id=user.id,
            correo=user.correo,
            rol=user.rol,
        )
