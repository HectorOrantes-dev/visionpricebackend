"""Caso de uso: registrar un nuevo usuario.

Reglas:
  - el correo debe ser único,
  - el rol debe existir (maestro_obra, contratista, arquitecto, ingeniero_civil),
  - la contraseña se guarda hasheada (nunca en claro),
  - opcionalmente se dispara el envío del código 2FA al correo.
"""
from dataclasses import dataclass

from src.features.register.domain.entities import NewUser, RegisteredUser
from src.features.register.domain.ports import RegisterUserRepository
from src.features.two_factor.domain.ports import TwoFactorPort
from src.shared.errors import Conflict, ValidationError
from src.shared.security import hash_password


@dataclass
class RegisterUserCommand:
    nombre: str
    correo: str
    contrasena: str
    rol: str
    telefono: str | None = None


class RegisterUser:
    def __init__(
        self,
        repo: RegisterUserRepository,
        two_factor: TwoFactorPort | None = None,
    ) -> None:
        self._repo = repo
        self._two_factor = two_factor

    async def execute(
        self, cmd: RegisterUserCommand, *, send_2fa: bool = True
    ) -> RegisteredUser:
        if len(cmd.contrasena) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")

        if await self._repo.email_exists(cmd.correo):
            raise Conflict("Ya existe un usuario con ese correo.")

        rol_id = await self._repo.get_role_id(cmd.rol)
        if rol_id is None:
            raise ValidationError(f"Rol inválido: {cmd.rol!r}.")

        user = await self._repo.create(
            NewUser(
                nombre=cmd.nombre,
                correo=cmd.correo,
                contrasena_hash=hash_password(cmd.contrasena),
                rol_id=rol_id,
                telefono=cmd.telefono,
            )
        )

        if send_2fa and self._two_factor is not None:
            await self._two_factor.send_code(user.correo)

        return user
