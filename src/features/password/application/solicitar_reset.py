"""Caso de uso: solicitar el código para restablecer la contraseña (forgot).

Si el correo existe, le pide al microservicio 2FA que genere y envíe el código.
NO revela si el correo existe (anti-enumeración): el router responde siempre
el mismo mensaje genérico.
"""
from src.features.password.domain.ports import PasswordUserRepository
from src.features.two_factor.domain.ports import TwoFactorPort


class SolicitarReset:
    def __init__(
        self, repo: PasswordUserRepository, two_factor: TwoFactorPort
    ) -> None:
        self._repo = repo
        self._two_factor = two_factor

    async def execute(self, correo: str) -> None:
        usuario_id = await self._repo.id_por_correo(correo)
        if usuario_id is not None:
            # El micro 2FA invalida códigos anteriores y manda uno nuevo.
            await self._two_factor.send_code(correo)
        # Si no existe, no hacemos nada (misma respuesta genérica en el router).
