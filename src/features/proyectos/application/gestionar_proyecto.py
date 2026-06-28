"""Casos de uso de proyectos (gestión e historial)."""
from dataclasses import dataclass

from src.features.proyectos.domain.entities import NuevoProyecto, Proyecto
from src.features.proyectos.domain.ports import ProyectoRepository
from src.shared.errors import NotFound, ValidationError

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
        return await self._repo.listar_de(usuario_id, estado)


class ObtenerProyecto:
    def __init__(self, repo: ProyectoRepository) -> None:
        self._repo = repo

    async def execute(self, proyecto_id: int, usuario_id: int) -> Proyecto:
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
    def __init__(self, repo: ProyectoRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: ActualizarProyectoCommand) -> Proyecto:
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
