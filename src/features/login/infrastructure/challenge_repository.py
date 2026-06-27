"""Adaptador SQLAlchemy del registro de desafíos 2FA."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.login.domain.entities import DesafioReciente
from src.features.login.domain.ports import TwoFactorChallengeRepository
from src.shared.models import Desafio2FA


class SqlAlchemyChallengeRepository(TwoFactorChallengeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(
        self,
        *,
        correo: str,
        usuario_id: int | None,
        proposito: str,
        ip_origen: str | None,
    ) -> None:
        self._session.add(
            Desafio2FA(
                correo=correo,
                usuario_id=usuario_id,
                proposito=proposito,
                ip_origen=ip_origen,
                estado="pendiente",
            )
        )
        await self._session.commit()

    async def obtener_ultimo(self, correo: str) -> DesafioReciente | None:
        result = await self._session.execute(
            select(Desafio2FA)
            .where(Desafio2FA.correo == correo)
            .order_by(Desafio2FA.id.desc())
            .limit(1)
        )
        desafio = result.scalar_one_or_none()
        if desafio is None:
            return None
        return DesafioReciente(
            id=desafio.id, intentos=desafio.intentos, estado=desafio.estado
        )

    async def actualizar(
        self,
        desafio_id: int,
        *,
        estado: str,
        intentos: int,
        verificado: bool = False,
    ) -> None:
        desafio = await self._session.get(Desafio2FA, desafio_id)
        if desafio is None:
            return
        desafio.estado = estado
        desafio.intentos = intentos
        if verificado:
            desafio.fecha_verificacion = datetime.now(timezone.utc)
        await self._session.commit()
