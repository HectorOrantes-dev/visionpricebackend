"""Servicio de auditoría: escribe en bitacora_auditoria.

Registra acciones sensibles (login, pagos, cotizaciones) con usuario, IP y
detalles. Se usa como dependencia en los routers:

    auditor: Auditor = Depends(get_auditor)
    await auditor.registrar(usuario_id=..., accion="login", ip_origen=...)
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.shared.models import BitacoraAuditoria


class Auditor:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def registrar(
        self,
        *,
        accion: str,
        usuario_id: int | None = None,
        tabla_afectada: str | None = None,
        registro_id: int | None = None,
        detalles: dict | None = None,
        ip_origen: str | None = None,
    ) -> None:
        self._session.add(
            BitacoraAuditoria(
                usuario_id=usuario_id,
                accion=accion,
                tabla_afectada=tabla_afectada,
                registro_id=registro_id,
                detalles=detalles,
                ip_origen=ip_origen,
            )
        )
        await self._session.commit()


def get_auditor(session: AsyncSession = Depends(get_session)) -> Auditor:
    return Auditor(session)
