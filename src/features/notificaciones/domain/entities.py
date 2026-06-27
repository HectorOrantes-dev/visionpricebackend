"""Entidades y catálogo de tipos de notificación."""
from dataclasses import dataclass
from datetime import datetime


class TipoNotificacion:
    """Catálogo de notificaciones acorde al modelo de negocio de VisionPrice."""

    SUSCRIPCION_POR_VENCER = "suscripcion_por_vencer"
    SUSCRIPCION_VENCIDA = "suscripcion_vencida"
    GRABACION_PROCESADA = "grabacion_procesada"
    GRABACION_ERROR = "grabacion_error"
    PRESUPUESTO_LISTO = "presupuesto_listo"
    BIENVENIDA = "bienvenida"

    TODOS = {
        SUSCRIPCION_POR_VENCER,
        SUSCRIPCION_VENCIDA,
        GRABACION_PROCESADA,
        GRABACION_ERROR,
        PRESUPUESTO_LISTO,
        BIENVENIDA,
    }


@dataclass
class NuevaNotificacion:
    usuario_id: int
    tipo: str
    titulo: str
    cuerpo: str  # SIN datos sensibles
    canal: str = "in_app"
    referencia_tipo: str | None = None
    referencia_id: int | None = None


@dataclass
class Notificacion:
    id: int
    usuario_id: int
    tipo: str
    titulo: str
    cuerpo: str
    canal: str
    estado: str
    leida: bool
    referencia_tipo: str | None
    referencia_id: int | None
    fecha_creacion: datetime
    fecha_envio: datetime | None


@dataclass
class SuscripcionUsuario:
    """Proyección para el job de vencimientos (sin PII)."""

    usuario_id: int
    plan_activo: str
    vigencia_hasta: datetime


@dataclass
class Destinatario:
    """Contacto TRANSITORIO para enviar. NUNCA se persiste en la notificación."""

    usuario_id: int
    correo: str
