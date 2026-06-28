"""Adaptador SQLAlchemy del repositorio de equipos."""
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.equipos.domain.entities import Equipo, Miembro
from src.features.equipos.domain.ports import EquipoRepository
from src.shared.models import Equipo as EquipoModel
from src.shared.models import EquipoMiembro, Usuario


def _to_equipo(m: EquipoModel) -> Equipo:
    return Equipo(
        id=m.id,
        nombre=m.nombre,
        propietario_id=m.propietario_id,
        fecha_creacion=m.fecha_creacion,
    )


class SqlAlchemyEquipoRepository(EquipoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, *, nombre: str, propietario_id: int) -> Equipo:
        fila = EquipoModel(nombre=nombre, propietario_id=propietario_id)
        self._session.add(fila)
        await self._session.commit()
        await self._session.refresh(fila)
        return _to_equipo(fila)

    async def listar_de(self, propietario_id: int) -> list[Equipo]:
        result = await self._session.execute(
            select(EquipoModel)
            .where(EquipoModel.propietario_id == propietario_id)
            .order_by(EquipoModel.id.desc())
        )
        return [_to_equipo(m) for m in result.scalars().all()]

    async def obtener(self, equipo_id: int) -> Equipo | None:
        fila = await self._session.get(EquipoModel, equipo_id)
        return _to_equipo(fila) if fila else None

    async def usuario_id_por_correo(self, correo: str) -> int | None:
        result = await self._session.execute(
            select(Usuario.id).where(Usuario.correo == correo)
        )
        return result.scalar_one_or_none()

    async def agregar_miembro(
        self, *, equipo_id: int, usuario_id: int, rol_en_equipo: str | None
    ) -> bool:
        ya = await self._session.get(EquipoMiembro, (equipo_id, usuario_id))
        if ya is not None:
            return False
        self._session.add(
            EquipoMiembro(
                equipo_id=equipo_id,
                usuario_id=usuario_id,
                rol_en_equipo=rol_en_equipo,
            )
        )
        await self._session.commit()
        return True

    async def quitar_miembro(self, *, equipo_id: int, usuario_id: int) -> bool:
        result = await self._session.execute(
            delete(EquipoMiembro).where(
                EquipoMiembro.equipo_id == equipo_id,
                EquipoMiembro.usuario_id == usuario_id,
            )
        )
        await self._session.commit()
        return result.rowcount > 0

    async def listar_miembros(self, equipo_id: int) -> list[Miembro]:
        result = await self._session.execute(
            select(EquipoMiembro, Usuario)
            .join(Usuario, Usuario.id == EquipoMiembro.usuario_id)
            .where(EquipoMiembro.equipo_id == equipo_id)
            .order_by(EquipoMiembro.fecha_asignacion)
        )
        return [
            Miembro(
                usuario_id=u.id,
                nombre=u.nombre,
                correo=u.correo,
                rol_en_equipo=em.rol_en_equipo,
                fecha_asignacion=em.fecha_asignacion,
            )
            for em, u in result.all()
        ]
