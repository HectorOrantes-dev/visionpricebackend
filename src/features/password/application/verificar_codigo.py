"""Caso de uso: verificar el código y emitir un reset_token de un solo uso.

OJO: el micro 2FA CONSUME el código al validarlo, por eso aquí devolvemos un
`reset_token` (JWT corto) que luego usa /reset — no se puede re-validar el código.
"""
from src.features.password.domain.ports import PasswordUserRepository
from src.features.two_factor.domain.ports import TwoFactorPort
from src.shared.errors import CodigoExpirado, CodigoInvalido
from src.shared.security import create_reset_token


def raise_por_reason(reason: str) -> None:
    if reason == "expired":
        raise CodigoExpirado("El código expiró. Solicita uno nuevo.")
    raise CodigoInvalido("Código inválido.")


class VerificarCodigo:
    def __init__(
        self,
        repo: PasswordUserRepository,
        two_factor: TwoFactorPort,
        token_minutes: int = 15,
    ) -> None:
        self._repo = repo
        self._two_factor = two_factor
        self._token_minutes = token_minutes

    async def execute(self, correo: str, code: str) -> str:
        result = await self._two_factor.verify_code(correo, code)
        if not result.valid:
            raise_por_reason(result.reason)

        usuario_id = await self._repo.id_por_correo(correo)
        if usuario_id is None:
            raise CodigoInvalido("Código inválido.")

        return create_reset_token(
            user_id=usuario_id, correo=correo, minutes=self._token_minutes
        )
