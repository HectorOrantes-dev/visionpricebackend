"""Caso de uso: restablecer la contraseña.

Acepta DOS formas de credencial (una de las dos):
  - `reset_token`: emitido por /verify-code (flujo recomendado).
  - `code`: valida el código directo con el micro 2FA (flujo simple).
"""
from dataclasses import dataclass

from src.features.password.application.verificar_codigo import raise_por_reason
from src.features.password.domain.ports import PasswordUserRepository
from src.features.two_factor.domain.ports import TwoFactorPort
from src.shared.errors import Unauthorized, ValidationError
from src.shared.security import decode_reset_token, hash_password


@dataclass
class RestablecerCommand:
    correo: str
    nueva_contrasena: str
    code: str | None = None
    reset_token: str | None = None


class Restablecer:
    def __init__(
        self, repo: PasswordUserRepository, two_factor: TwoFactorPort
    ) -> None:
        self._repo = repo
        self._two_factor = two_factor

    async def execute(self, cmd: RestablecerCommand) -> int:
        if len(cmd.nueva_contrasena) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

        if cmd.reset_token:
            usuario_id = await self._por_token(cmd.reset_token, cmd.correo)
        elif cmd.code:
            usuario_id = await self._por_codigo(cmd.correo, cmd.code)
        else:
            raise ValidationError("Proporciona reset_token o code.")

        await self._repo.actualizar_password(
            usuario_id, hash_password(cmd.nueva_contrasena)
        )
        return usuario_id

    async def _por_token(self, reset_token: str, correo: str) -> int:
        payload = decode_reset_token(reset_token)
        if payload.get("correo") != correo:
            raise Unauthorized("El token no corresponde a ese correo.")
        return int(payload["sub"])

    async def _por_codigo(self, correo: str, code: str) -> int:
        result = await self._two_factor.verify_code(correo, code)
        if not result.valid:
            raise_por_reason(result.reason)
        usuario_id = await self._repo.id_por_correo(correo)
        if usuario_id is None:
            raise Unauthorized("No se pudo restablecer la contraseña.")
        return usuario_id
