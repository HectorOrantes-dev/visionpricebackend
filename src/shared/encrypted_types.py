"""Tipo SQLAlchemy que cifra/descifra de forma transparente.

Es el "interceptor con cipher" de la arquitectura: se sitúa entre la entity
(modelo) y la BD. Al ESCRIBIR cifra (datos en reposo); al LEER descifra (datos
en tránsito hacia el service/DTO). El resto del código trabaja con texto plano.

Uso en un modelo:
    telefono: Mapped[str | None] = mapped_column(EncryptedString(255), ...)

Nota: el valor cifrado (token Fernet) es mucho más largo que el original, así
que la columna debe ser amplia (Text o String grande).
"""
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from src.shared.crypto import get_cipher


class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):  # escritura -> BD
        if value is None:
            return None
        return get_cipher().encrypt(str(value))

    def process_result_value(self, value, dialect):  # lectura BD -> app
        if value is None:
            return None
        return get_cipher().decrypt(value)
