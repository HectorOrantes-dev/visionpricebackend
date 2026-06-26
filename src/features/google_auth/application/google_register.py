"""Caso de uso: register con Google.

Verifica el id_token y exige un `rol` (Google no lo provee). Si el correo ya
existe, se comporta como login (idempotente) y vincula el google_sub.
"""
from dataclasses import dataclass

from src.features.google_auth.application.google_login import AuthToken
from src.features.google_auth.domain.ports import (
    GoogleIdentityVerifier,
    GoogleUserRepository,
)
from src.shared.errors import Unauthorized, ValidationError
from src.shared.security import create_access_token


@dataclass
class GoogleRegisterCommand:
    id_token: str
    rol: str


class GoogleRegister:
    def __init__(
        self, verifier: GoogleIdentityVerifier, repo: GoogleUserRepository
    ) -> None:
        self._verifier = verifier
        self._repo = repo

    async def execute(self, cmd: GoogleRegisterCommand) -> AuthToken:
        identity = self._verifier.verify(cmd.id_token)
        if not identity.email_verified:
            raise Unauthorized("El correo de Google no está verificado.")

        existente = await self._repo.get_by_correo(identity.email)
        if existente is not None:
            # Ya tenía cuenta: lo tratamos como login y vinculamos el sub.
            if not existente.activo:
                raise Unauthorized("La cuenta está desactivada.")
            if existente.google_sub is None:
                await self._repo.vincular_google(existente.id, identity.sub)
            user = existente
            es_nuevo = False
        else:
            rol_id = await self._repo.get_role_id(cmd.rol)
            if rol_id is None:
                raise ValidationError(f"Rol inválido: {cmd.rol!r}.")
            user = await self._repo.crear_google(
                nombre=identity.nombre,
                correo=identity.email,
                rol_id=rol_id,
                google_sub=identity.sub,
            )
            es_nuevo = True

        token = create_access_token(
            user_id=user.id, email=user.correo, rol=user.rol
        )
        return AuthToken(
            access_token=token,
            token_type="bearer",
            user_id=user.id,
            correo=user.correo,
            rol=user.rol,
            es_nuevo=es_nuevo,
        )
