"""Adaptadores del puerto PushNotifier.

- `FcmPushNotifier`: envía push vía Firebase Cloud Messaging. Los device tokens
  se obtienen al vuelo del repositorio de dispositivos (no se persisten en la
  notificación). Si FCM reporta un token inválido, se desactiva.
- `NullPushNotifier`: no hace nada (cuando Firebase no está configurado).

`firebase_admin` se importa de forma perezosa para no acoplar el arranque.
"""
import logging

from src.features.dispositivos.domain.ports import DispositivoRepository
from src.features.notificaciones.domain.ports import PushNotifier
from src.shared.firebase import ensure_firebase

_log = logging.getLogger("notificaciones.push")


class NullPushNotifier(PushNotifier):
    async def notificar(
        self, usuario_id, titulo, cuerpo, *, data=None
    ) -> int:
        return 0


class FcmPushNotifier(PushNotifier):
    def __init__(self, dispositivos: DispositivoRepository) -> None:
        self._dispositivos = dispositivos

    async def notificar(
        self,
        usuario_id: int,
        titulo: str,
        cuerpo: str,
        *,
        data: dict[str, str] | None = None,
    ) -> int:
        tokens = await self._dispositivos.tokens_activos(usuario_id)
        if not tokens:
            return 0

        ensure_firebase()
        from firebase_admin import messaging  # import perezoso

        mensaje = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title=titulo, body=cuerpo),
            data={k: str(v) for k, v in (data or {}).items()},
        )

        try:
            resp = messaging.send_each_for_multicast(mensaje)
        except Exception as exc:  # noqa: BLE001
            _log.warning("Fallo enviando push FCM: %s", exc)
            return 0

        # Limpieza: desactiva tokens que FCM reporta como inválidos.
        for idx, r in enumerate(resp.responses):
            if not r.success and isinstance(
                r.exception,
                (messaging.UnregisteredError, messaging.SenderIdMismatchError),
            ):
                await self._dispositivos.desactivar_token(tokens[idx])

        return resp.success_count
