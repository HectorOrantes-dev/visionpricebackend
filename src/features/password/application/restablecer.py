"""Caso de uso: restablecer la contraseña con el código (reset).

Confía en el `valid` del microservicio 2FA (fuente de verdad del código). Si es
válido, guarda la nueva contraseña hasheada.
"""
from dataclasses import dataclass

from src.features.password.domain.ports import PasswordUserRepository
from src.features.two_factor.domain.ports import TwoFactorPort
from src.shared.errors import TwoFactorInvalid, Unauthorized, ValidationError
from src.shared.security import hash_password


@dataclass
class RestablecerCommand:
    correo: str
    code: str
    nueva_contrasena: str


class Restablecer:
    def __init__(
        self, repo: PasswordUserRepository, two_factor: TwoFactorPort
    ) -> None:
        self._repo = repo
        self._two_factor = two_factor

    async def execute(self, cmd: RestablecerCommand) -> int:
        if len(cmd.nueva_contrasena) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

        result = await self._two_factor.verify_code(cmd.correo, cmd.code)
        if not result.valid:
            raise TwoFactorInvalid(
                "Código de verificación inválido.",
                details={"reason": result.reason},
            )

        usuario_id = await self._repo.id_por_correo(cmd.correo)
        if usuario_id is None:
            # Si el código era válido, el usuario debería existir; genérico.
            raise Unauthorized("No se pudo restablecer la contraseña.")

        await self._repo.actualizar_password(
            usuario_id, hash_password(cmd.nueva_contrasena)
        )
        return usuario_id
