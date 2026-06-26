"""Caso de uso: paso 2 del login (verificar código 2FA y emitir JWT).

Confía en `valid` del microservicio 2FA: si es true, emite el access token
firmado con el secreto compartido con el microservicio de Pagos. Registra el
resultado del desafío (intentos/estado) para auditoría.
"""
from dataclasses import dataclass

from src.features.login.domain.ports import (
    LoginUserRepository,
    TwoFactorChallengeRepository,
)
from src.features.two_factor.domain.ports import TwoFactorPort
from src.shared.errors import TwoFactorInvalid, Unauthorized
from src.shared.security import create_access_token


@dataclass
class VerifyCommand:
    correo: str
    code: str


@dataclass
class AuthToken:
    access_token: str
    token_type: str
    user_id: int
    correo: str
    rol: str


class VerifyTwoFactor:
    def __init__(
        self,
        repo: LoginUserRepository,
        two_factor: TwoFactorPort,
        challenges: TwoFactorChallengeRepository | None = None,
    ) -> None:
        self._repo = repo
        self._two_factor = two_factor
        self._challenges = challenges

    async def execute(self, cmd: VerifyCommand) -> AuthToken:
        result = await self._two_factor.verify_code(cmd.correo, cmd.code)

        if self._challenges is not None:
            await self._challenges.registrar_resultado(
                cmd.correo, exito=result.valid
            )

        if not result.valid:
            raise TwoFactorInvalid(
                "Código de verificación inválido.",
                details={"reason": result.reason},
            )

        user = await self._repo.get_by_email(cmd.correo)
        if user is None or not user.activo:
            raise Unauthorized("Usuario no válido para emitir sesión.")

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
