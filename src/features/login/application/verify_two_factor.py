"""Caso de uso: paso 2 del login (verificar código 2FA y emitir JWT).

Responsabilidades:
  - El **microservicio 2FA** es la fuente de verdad del código (genera, expira,
    single-use, valida). Aquí solo confiamos en su `valid`.
  - El registro en `desafios_2fa` es **auditoría best-effort**: si hay un desafío
    pendiente, sumamos intento / aplicamos rate-limit (bloqueado → 429) y dejamos
    rastro (estado, IP). Si NO hay desafío, NO se bloquea: se confía en el micro.

El JWT se firma con el secreto compartido con el microservicio de Pagos.
"""
from dataclasses import dataclass

from src.features.login.domain.ports import (
    LoginUserRepository,
    TwoFactorChallengeRepository,
)
from src.features.two_factor.domain.ports import TwoFactorPort
from src.shared.errors import TooManyAttempts, TwoFactorInvalid, Unauthorized
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
        # Auditoría/rate-limit best-effort sobre el último desafío (si existe).
        desafio = None
        if self._challenges is not None:
            desafio = await self._challenges.obtener_ultimo(cmd.correo)
            if desafio is not None:
                # Bloqueo pegajoso: una vez bloqueado, sigue bloqueado hasta
                # que se pida un código nuevo (que crea otro desafío).
                if desafio.estado == "bloqueado" or (
                    desafio.estado == "pendiente"
                    and desafio.intentos >= self._max_intentos
                ):
                    if desafio.estado != "bloqueado":
                        await self._challenges.actualizar(
                            desafio.id,
                            estado="bloqueado",
                            intentos=desafio.intentos,
                        )
                    raise TooManyAttempts(
                        "Demasiados intentos. Solicita un código nuevo."
                    )

        # Fuente de verdad del código: el microservicio 2FA.
        result = await self._two_factor.verify_code(cmd.correo, cmd.code)

        # Rastro del resultado (solo si el desafío sigue pendiente).
        if (
            desafio is not None
            and desafio.estado == "pendiente"
            and self._challenges is not None
        ):
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
