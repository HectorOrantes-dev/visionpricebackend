"""Puertos de la feature notificaciones."""
from abc import ABC, abstractmethod

from src.features.notificaciones.domain.entities import (
    Destinatario,
    Notificacion,
    NuevaNotificacion,
    SuscripcionUsuario,
)


class NotificacionRepository(ABC):
    @abstractmethod
    async def crear(self, nueva: NuevaNotificacion) -> Notificacion:
        ...

    @abstractmethod
    async def existe_reciente(
        self, usuario_id: int, tipo: str, dentro_dias: int
    ) -> bool:
        """True si ya hay una notificación de ese tipo creada en la ventana (dedupe)."""

    @abstractmethod
    async def listar_por_usuario(
        self, usuario_id: int, solo_no_leidas: bool = False
    ) -> list[Notificacion]:
        ...

    @abstractmethod
    async def marcar_leida(self, notificacion_id: int, usuario_id: int) -> bool:
        ...

    @abstractmethod
    async def marcar_enviada(self, notificacion_id: int) -> None:
        ...

    @abstractmethod
    async def suscripciones_por_vencer(
        self, dias: int
    ) -> list[SuscripcionUsuario]:
        ...

    @abstractmethod
    async def suscripciones_vencidas(self) -> list[SuscripcionUsuario]:
        ...

    @abstractmethod
    async def get_destinatario(self, usuario_id: int) -> Destinatario | None:
        """Contacto TRANSITORIO para enviar (no se persiste en la notificación)."""


class NotificationSender(ABC):
    """Canal de envío por email. El in-app es solo el registro en BD."""

    @abstractmethod
    async def send(self, *, correo: str, titulo: str, cuerpo: str) -> None:
        ...


class PushNotifier(ABC):
    """Canal de push (FCM). Resuelve los device tokens del usuario al vuelo."""

    @abstractmethod
    async def notificar(
        self,
        usuario_id: int,
        titulo: str,
        cuerpo: str,
        *,
        data: dict[str, str] | None = None,
    ) -> int:
        """Envía el push y devuelve cuántos dispositivos lo recibieron."""
