"""Filtros de enmascarado para datos sensibles en SALIDA (el "filter").

El cifrado protege en reposo; estos filtros deciden CUÁNTO se revela cuando un
dato sale en una respuesta (p. ej. exponer un teléfono o correo de otro usuario
de forma parcial). El dueño del dato normalmente ve el valor completo; al
exponerlo a terceros se enmascara.
"""


def mask_value(value: str | None, *, visible: int = 4, mask_char: str = "*") -> str | None:
    """Deja visibles los últimos `visible` caracteres; el resto enmascarado."""
    if not value:
        return value
    if len(value) <= visible:
        return mask_char * len(value)
    return mask_char * (len(value) - visible) + value[-visible:]


def mask_phone(phone: str | None) -> str | None:
    """Teléfono: muestra solo los últimos 4 dígitos. '5512345678' -> '******5678'."""
    return mask_value(phone, visible=4)


def mask_email(email: str | None) -> str | None:
    """Correo: 'hector@dominio.com' -> 'h****@dominio.com'."""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        visible = local
    else:
        visible = local[0] + "*" * (len(local) - 1)
    return f"{visible}@{domain}"
