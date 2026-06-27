"""Puerto del repositorio de dispositivos (device tokens FCM)."""
from abc import ABC, abstractmethod


class DispositivoRepository(ABC):
    @abstractmethod
    async def registrar(
        self, *, usuario_id: int, token: str, plataforma: str
    ) -> None:
        """Alta o actualización (upsert) del device token del usuario."""

    @abstractmethod
    async def eliminar(self, *, usuario_id: int, token: str) -> None:
        ...

    @abstractmethod
    async def tokens_activos(self, usuario_id: int) -> list[str]:
        ...

    @abstractmethod
    async def desactivar_token(self, token: str) -> None:
        """Marca un token como inactivo (FCM lo reportó inválido)."""
