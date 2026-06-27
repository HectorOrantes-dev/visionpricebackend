"""Adaptador SQLAlchemy del repositorio de dispositivos."""
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.dispositivos.domain.ports import DispositivoRepository
from src.shared.models import Dispositivo
from src.shared.timeutils import utcnow


class SqlAlchemyDispositivoRepository(DispositivoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(
        self, *, usuario_id: int, token: str, plataforma: str
    ) -> None:
        # Upsert por token: un mismo dispositivo puede cambiar de dueño/estado.
        existente = await self._session.execute(
            select(Dispositivo).where(Dispositivo.token == token)
        )
        fila = existente.scalar_one_or_none()
        ahora = utcnow()
        if fila is None:
            self._session.add(
                Dispositivo(
                    usuario_id=usuario_id,
                    token=token,
                    plataforma=plataforma,
                    activo=True,
                )
            )
        else:
            fila.usuario_id = usuario_id
            fila.plataforma = plataforma
            fila.activo = True
            fila.fecha_actualizacion = ahora
        await self._session.commit()

    async def eliminar(self, *, usuario_id: int, token: str) -> None:
        await self._session.execute(
            delete(Dispositivo).where(
                Dispositivo.token == token, Dispositivo.usuario_id == usuario_id
            )
        )
        await self._session.commit()

    async def tokens_activos(self, usuario_id: int) -> list[str]:
        result = await self._session.execute(
            select(Dispositivo.token).where(
                Dispositivo.usuario_id == usuario_id,
                Dispositivo.activo.is_(True),
            )
        )
        return [t for (t,) in result.all()]

    async def desactivar_token(self, token: str) -> None:
        await self._session.execute(
            update(Dispositivo)
            .where(Dispositivo.token == token)
            .values(activo=False)
        )
        await self._session.commit()
