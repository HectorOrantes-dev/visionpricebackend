"""Adaptador SQLAlchemy del registro de desafíos 2FA."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def registrar_resultado(self, correo: str, *, exito: bool) -> None:
        result = await self._session.execute(
            select(Desafio2FA)
            .where(Desafio2FA.correo == correo, Desafio2FA.estado == "pendiente")
            .order_by(Desafio2FA.id.desc())
            .limit(1)
        )
        desafio = result.scalar_one_or_none()
        if desafio is None:
            return
        desafio.intentos += 1
        if exito:
            desafio.estado = "verificado"
            desafio.fecha_verificacion = datetime.now(timezone.utc)
        await self._session.commit()
