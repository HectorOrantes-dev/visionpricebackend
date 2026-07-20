"""Construcción de títulos/cuerpos por tipo. SIN datos sensibles."""
from datetime import datetime

from src.features.notificaciones.domain.entities import TipoNotificacion


def vencimiento_por_vencer(plan: str, vigencia: datetime) -> tuple[str, str]:
    return (
        "Tu suscripción está por vencer",
        f"Tu plan {plan} vence el {vigencia.date().isoformat()}. "
        "Renueva para no perder el acceso.",
    )


def vencimiento_vencido(plan: str, vigencia: datetime) -> tuple[str, str]:
    return (
        "Tu suscripción venció",
        f"Tu plan {plan} venció el {vigencia.date().isoformat()}. "
        "Renueva para reactivar tu cuenta.",
    )


# Textos por defecto para los eventos emitidos por otras features/microservicios.
DEFAULTS: dict[str, tuple[str, str]] = {
    TipoNotificacion.GRABACION_PROCESADA: (
        "Tu grabación está lista",
        "Procesamos tu audio: ya tienes la transcripción y los datos extraídos.",
    ),
    TipoNotificacion.GRABACION_ERROR: (
        "Error al procesar tu grabación",
        "No pudimos procesar tu audio. Intenta subirlo de nuevo.",
    ),
    TipoNotificacion.PRESUPUESTO_LISTO: (
        "Tu presupuesto está listo",
        "Generamos tu presupuesto. Ya puedes revisarlo y exportarlo.",
    ),
    TipoNotificacion.SUSCRIPCION_ACTIVADA: (
        "¡Tu suscripción está activa!",
        "Tu plan quedó activo. Ya tienes acceso a todas las funciones de VisionPrice.",
    ),
    TipoNotificacion.INVITACION_PROYECTO: (
        "Nuevo colaborador en tu proyecto",
        "Alguien se unió a un proyecto que administras. Ábrelo para ver los detalles.",
    ),
    TipoNotificacion.BIENVENIDA: (
        "¡Bienvenido a VisionPrice!",
        "Tu cuenta está lista. Empieza a crear tus presupuestos por voz.",
    ),
}
