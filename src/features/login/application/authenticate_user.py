"""Caso de uso: paso 1 del login (usuario + contraseña).

Si las credenciales son correctas, se dispara el envío del código 2FA y se
registra el desafío (auditoría/intentos/IP). NO se emite token aún.
"""
from dataclasses import dataclass

from src.features.login.domain.ports import (
    LoginUserRepository,
    TwoFactorChallengeRepository,
)
from src.features.two_factor.domain.ports import TwoFactorPort
from src.shared.errors import InvalidCredentials, Unauthorized
from src.shared.security import verify_password


@dataclass
class LoginCommand:
    correo: str
    contrasena: str
    ip_origen: str | None = None


@dataclass
class LoginChallenge:
    correo: str
    two_factor_sent: bool


class AuthenticateUser:
    def __init__(
        self,
        repo: LoginUserRepository,
        two_factor: TwoFactorPort,
        challenges: TwoFactorChallengeRepository | None = None,
    ) -> None:
        self._repo = repo
        self._two_factor = two_factor
        self._challenges = challenges

    async def execute(self, cmd: LoginCommand) -> LoginChallenge:
        user = await self._repo.get_by_email(cmd.correo)
        # Mensaje genérico para no filtrar si el correo existe.
        if user is None or not verify_password(
            cmd.contrasena, user.contrasena_hash
        ):
            raise InvalidCredentials("Correo o contraseña incorrectos.")

        if not user.activo:
            raise Unauthorized("La cuenta está desactivada.")

        await self._two_factor.send_code(user.correo)

        if self._challenges is not None:
            await self._challenges.crear(
                correo=user.correo,
                usuario_id=user.id,
                proposito="login",
                ip_origen=cmd.ip_origen,
            )

        return LoginChallenge(correo=user.correo, two_factor_sent=True)
