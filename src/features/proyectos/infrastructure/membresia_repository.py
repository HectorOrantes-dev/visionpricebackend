"""Adaptador SQLAlchemy de membresía de proyectos."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.proyectos.domain.entities import Miembro
from src.features.proyectos.domain.ports import MembresiaRepository
from src.shared.models import Proyecto, ProyectoColaborador, Usuario


class SqlAlchemyMembresiaRepository(MembresiaRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def puede_acceder(self, proyecto_id: int, usuario_id: int) -> bool:
        if await self.es_dueno(proyecto_id, usuario_id):
            return True
        return await self.es_miembro(proyecto_id, usuario_id)

    async def es_dueno(self, proyecto_id: int, usuario_id: int) -> bool:
        row = await self._session.execute(
            select(Proyecto.id).where(
                Proyecto.id == proyecto_id,
                Proyecto.usuario_id == usuario_id,
            )
        )
        return row.scalar_one_or_none() is not None

    async def es_miembro(self, proyecto_id: int, usuario_id: int) -> bool:
        row = await self._session.execute(
            select(ProyectoColaborador.proyecto_id).where(
                ProyectoColaborador.proyecto_id == proyecto_id,
                ProyectoColaborador.usuario_id == usuario_id,
            )
        )
        return row.scalar_one_or_none() is not None

    async def agregar(
        self, proyecto_id: int, usuario_id: int, rol: str
    ) -> Miembro:
        fila = ProyectoColaborador(
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            rol_en_proyecto=rol,
        )
        self._session.add(fila)
        await self._session.commit()
        await self._session.refresh(fila)
        return Miembro(
            proyecto_id=fila.proyecto_id,
            usuario_id=fila.usuario_id,
            rol_en_proyecto=fila.rol_en_proyecto,
            fecha_asignacion=fila.fecha_asignacion,
        )

    async def listar(self, proyecto_id: int) -> list[Miembro]:
        result = await self._session.execute(
            select(ProyectoColaborador, Usuario.nombre, Usuario.correo)
            .join(Usuario, Usuario.id == ProyectoColaborador.usuario_id)
            .where(ProyectoColaborador.proyecto_id == proyecto_id)
            .order_by(ProyectoColaborador.fecha_asignacion)
        )
        miembros = []
        for col, nombre, correo in result.all():
            miembros.append(
                Miembro(
                    proyecto_id=col.proyecto_id,
                    usuario_id=col.usuario_id,
                    rol_en_proyecto=col.rol_en_proyecto,
                    fecha_asignacion=col.fecha_asignacion,
                    nombre=nombre,
                    correo=correo,
                )
            )
        return miembros

    async def quitar(self, proyecto_id: int, usuario_id: int) -> bool:
        fila = await self._session.get(
            ProyectoColaborador, (proyecto_id, usuario_id)
        )
        if fila is None:
            return False
        await self._session.delete(fila)
        await self._session.commit()
        return True
