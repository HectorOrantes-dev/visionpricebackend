"""Adaptador SQLAlchemy del repositorio de proyectos."""
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.proyectos.domain.entities import NuevoProyecto, Proyecto
from src.features.proyectos.domain.ports import ProyectoRepository
from src.shared.models import Presupuesto
from src.shared.models import Proyecto as ProyectoModel
from src.shared.models import ProyectoColaborador

_CAMPOS = {"nombre", "direccion", "latitud", "longitud", "estado"}


def _to_entity(m: ProyectoModel, total: int = 0, es_dueno: bool = True) -> Proyecto:
    return Proyecto(
        id=m.id,
        usuario_id=m.usuario_id,
        nombre=m.nombre,
        direccion=m.direccion,
        latitud=float(m.latitud) if m.latitud is not None else None,
        longitud=float(m.longitud) if m.longitud is not None else None,
        estado=m.estado,
        fecha_creacion=m.fecha_creacion,
        total_presupuestos=total,
        es_dueno=es_dueno,
    )


class SqlAlchemyProyectoRepository(ProyectoRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, nuevo: NuevoProyecto) -> Proyecto:
        fila = ProyectoModel(
            usuario_id=nuevo.usuario_id,
            nombre=nuevo.nombre,
            direccion=nuevo.direccion,
            latitud=nuevo.latitud,
            longitud=nuevo.longitud,
        )
        self._session.add(fila)
        await self._session.commit()
        await self._session.refresh(fila)
        return _to_entity(fila)

    async def listar_de(
        self, usuario_id: int, estado: str | None = None
    ) -> list[Proyecto]:
        """Devuelve proyectos propios + donde el usuario es colaborador.

        Los propios tienen es_dueno=True; los compartidos es_dueno=False.
        Se evitan duplicados: si alguien es dueño Y colaborador (no debería ocurrir,
        pero en previsión), se prefiere is_dueno=True.
        """
        stmt = (
            select(ProyectoModel, func.count(Presupuesto.id))
            .outerjoin(Presupuesto, Presupuesto.proyecto_id == ProyectoModel.id)
            .where(
                or_(
                    ProyectoModel.usuario_id == usuario_id,
                    ProyectoModel.id.in_(
                        select(ProyectoColaborador.proyecto_id).where(
                            ProyectoColaborador.usuario_id == usuario_id
                        )
                    ),
                )
            )
            .group_by(ProyectoModel.id)
            .order_by(ProyectoModel.id.desc())
        )
        if estado is not None:
            stmt = stmt.where(ProyectoModel.estado == estado)

        result = await self._session.execute(stmt)
        filas = result.all()

        # Determinar es_dueno para cada fila.
        return [
            _to_entity(m, total, es_dueno=(m.usuario_id == usuario_id))
            for m, total in filas
        ]

    async def obtener(self, proyecto_id: int, usuario_id: int) -> Proyecto | None:
        """Devuelve el proyecto independientemente de si es dueño o colaborador.

        El guard de acceso (puede_acceder) se hace en el caso de uso antes de
        llamar este método, por lo que aquí solo buscamos por id.
        """
        result = await self._session.execute(
            select(ProyectoModel, func.count(Presupuesto.id))
            .outerjoin(Presupuesto, Presupuesto.proyecto_id == ProyectoModel.id)
            .where(ProyectoModel.id == proyecto_id)
            .group_by(ProyectoModel.id)
        )
        fila = result.first()
        if fila is None:
            return None
        m, total = fila
        return _to_entity(m, total, es_dueno=(m.usuario_id == usuario_id))

    async def actualizar(
        self, proyecto_id: int, usuario_id: int, cambios: dict
    ) -> Proyecto | None:
        """Solo el dueño puede actualizar (validado en el caso de uso)."""
        fila = await self._session.get(ProyectoModel, proyecto_id)
        if fila is None or fila.usuario_id != usuario_id:
            return None
        for campo, valor in cambios.items():
            if campo in _CAMPOS and valor is not None:
                setattr(fila, campo, valor)
        await self._session.commit()
        await self._session.refresh(fila)
        return _to_entity(fila, es_dueno=True)
