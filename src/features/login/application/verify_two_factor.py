"""Caso de uso: paso 2 del login (verificar código 2FA y emitir JWT).

Reglas (independientes de la IP — la IP es sólo auditoría):
  - debe existir un desafío PENDIENTE para el correo,
  - límite de `max_intentos` por desafío → estado `bloqueado` (429),
  - si el micro 2FA dice `valid` → estado `verificado` y se emite el JWT,
  - si `reason == expired` → estado `expirado`.

El JWT se firma con el secreto compartido con el microservicio de Pagos.
"""
from dataclasses import dataclass

from src.features.login.domain.ports import (
    LoginUserRepository,
    TwoFactorChallengeRepository,
)
from src.features.two_factor.domain.ports import TwoFactorPort
from src.shared.errors import (
    NoActiveChallenge,
    TooManyAttempts,
    TwoFactorInvalid,
    Unauthorized,
)
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
        max_intentos: int = 5,
    ) -> None:
        self._repo = repo
        self._two_factor = two_factor
        self._challenges = challenges
        self._max_intentos = max_intentos

    async def execute(self, cmd: VerifyCommand) -> AuthToken:
        desafio = None
        if self._challenges is not None:
            desafio = await self._challenges.obtener_pendiente(cmd.correo)
            if desafio is None:
                raise NoActiveChallenge("No hay un desafío 2FA activo.")
            if desafio.intentos >= self._max_intentos:
                await self._challenges.actualizar(
                    desafio.id, estado="bloqueado", intentos=desafio.intentos
                )
                raise TooManyAttempts("Demasiados intentos. Solicita un código nuevo.")

        result = await self._two_factor.verify_code(cmd.correo, cmd.code)

        if desafio is not None and self._challenges is not None:
            intentos = desafio.intentos + 1
            if result.valid:
                await self._challenges.actualizar(
                    desafio.id,
                    estado="verificado",
                    intentos=intentos,
                    verificado=True,
                )
            else:
                estado = "expirado" if result.reason == "expired" else "pendiente"
                await self._challenges.actualizar(
                    desafio.id, estado=estado, intentos=intentos
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
