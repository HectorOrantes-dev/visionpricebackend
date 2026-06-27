"""Cifrado simétrico de datos sensibles (el "cipher" de la arquitectura).

Usa Fernet (AES-128-CBC + HMAC) de `cryptography`. Soporta varias claves
(MultiFernet) para rotación: la primera cifra, todas se prueban al descifrar.

Si no hay clave configurada, se usa un NullCipher (passthrough) SOLO para que
el entorno local arranque; en producción DEBES definir DATA_ENCRYPTION_KEY.
"""
import warnings
from functools import lru_cache
from typing import Protocol

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from src.core.config import settings
from src.shared.errors import DomainError


class CipherError(DomainError):
    code = "cipher_error"
    status_code = 500


class Cipher(Protocol):
    def encrypt(self, plaintext: str) -> str: ...
    def decrypt(self, token: str) -> str: ...


class FernetCipher:
    def __init__(self, keys: list[str]) -> None:
        self._fernet = MultiFernet([Fernet(k.encode()) for k in keys])

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken as exc:
            raise CipherError(
                "No se pudo descifrar un dato (clave incorrecta o dato corrupto)."
            ) from exc


class NullCipher:
    """Passthrough — NO cifra. Solo para dev sin clave configurada."""

    def encrypt(self, plaintext: str) -> str:
        return plaintext

    def decrypt(self, token: str) -> str:
        return token


@lru_cache
def get_cipher() -> Cipher:
    keys = settings.data_encryption_keys
    if keys:
        return FernetCipher(keys)
    warnings.warn(
        "DATA_ENCRYPTION_KEY no configurada: los datos sensibles NO se cifran. "
        "Configúrala en producción.",
        stacklevel=2,
    )
    return NullCipher()
