"""Casos de uso de proyectos (gestión e historial)."""
from dataclasses import dataclass

from src.features.proyectos.domain.entities import NuevoProyecto, Proyecto
from src.features.proyectos.domain.ports import MembresiaRepository, ProyectoRepository
from src.shared.errors import Forbidden, NotFound, ValidationError

_ESTADOS = {"activo", "finalizado", "cancelado"}


@dataclass
class CrearProyectoCommand:
    usuario_id: int
    nombre: str
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None


class CrearProyecto:
    def __init__(self, repo: ProyectoRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: CrearProyectoCommand) -> Proyecto:
        if not cmd.nombre.strip():
            raise ValidationError("El nombre del proyecto es obligatorio.")
        return await self._repo.crear(
            NuevoProyecto(
                usuario_id=cmd.usuario_id,
                nombre=cmd.nombre,
                direccion=cmd.direccion,
                latitud=cmd.latitud,
                longitud=cmd.longitud,
            )
        )


class ListarProyectos:
    def __init__(self, repo: ProyectoRepository) -> None:
        self._repo = repo

    async def execute(
        self, usuario_id: int, estado: str | None = None
    ) -> list[Proyecto]:
        if estado is not None and estado not in _ESTADOS:
            raise ValidationError(f"Estado inválido: {estado!r}.")
        # listar_de devuelve propios + compartidos (marcados con es_dueno=False)
        return await self._repo.listar_de(usuario_id, estado)


class ObtenerProyecto:
    def __init__(self, repo: ProyectoRepository, membresia: MembresiaRepository) -> None:
        self._repo = repo
        self._mem = membresia

    async def execute(self, proyecto_id: int, usuario_id: int) -> Proyecto:
        # Acceso: dueño O colaborador.
        if not await self._mem.puede_acceder(proyecto_id, usuario_id):
            raise NotFound("Proyecto no encontrado.")  # 404 para no filtrar existencia
        proyecto = await self._repo.obtener(proyecto_id, usuario_id)
        if proyecto is None:
            raise NotFound("Proyecto no encontrado.")
        return proyecto


@dataclass
class ActualizarProyectoCommand:
    proyecto_id: int
    usuario_id: int
    cambios: dict


class ActualizarProyecto:
    def __init__(self, repo: ProyectoRepository, membresia: MembresiaRepository) -> None:
        self._repo = repo
        self._mem = membresia

    async def execute(self, cmd: ActualizarProyectoCommand) -> Proyecto:
        # Solo el dueño puede editar el proyecto.
        if not await self._mem.es_dueno(cmd.proyecto_id, cmd.usuario_id):
            raise Forbidden("Solo el dueño puede modificar el proyecto.")
        estado = cmd.cambios.get("estado")
        if estado is not None and estado not in _ESTADOS:
            raise ValidationError(f"Estado inválido: {estado!r}.")
        if not cmd.cambios:
            raise ValidationError("No hay cambios que aplicar.")
        proyecto = await self._repo.actualizar(
            cmd.proyecto_id, cmd.usuario_id, cmd.cambios
        )
        if proyecto is None:
            raise NotFound("Proyecto no encontrado.")
        return proyecto
