"""Casos de uso de equipos / plantilla.

Solo el PROPIETARIO del equipo (arquitecto/ing. civil que lo creó) puede
administrar su plantilla. La autorización por ROL ya la hace el router con
`require_roles`; aquí se valida además la PROPIEDAD del recurso.
"""
from dataclasses import dataclass

from src.features.equipos.domain.entities import Equipo, Miembro
from src.features.equipos.domain.ports import EquipoRepository
from src.shared.errors import Conflict, Forbidden, NotFound, ValidationError


class CrearEquipo:
    def __init__(self, repo: EquipoRepository) -> None:
        self._repo = repo

    async def execute(self, *, nombre: str, propietario_id: int) -> Equipo:
        if not nombre.strip():
            raise ValidationError("El nombre del equipo es obligatorio.")
        return await self._repo.crear(nombre=nombre, propietario_id=propietario_id)


class ListarMisEquipos:
    def __init__(self, repo: EquipoRepository) -> None:
        self._repo = repo

    async def execute(self, propietario_id: int) -> list[Equipo]:
        return await self._repo.listar_de(propietario_id)


async def _equipo_propio(repo: EquipoRepository, equipo_id: int, usuario_id: int) -> Equipo:
    equipo = await repo.obtener(equipo_id)
    if equipo is None:
        raise NotFound("Equipo no encontrado.")
    if equipo.propietario_id != usuario_id:
        raise Forbidden("No eres el propietario de este equipo.")
    return equipo


@dataclass
class AgregarMiembroCommand:
    equipo_id: int
    propietario_id: int
    correo: str
    rol_en_equipo: str | None = None


class AgregarMiembro:
    def __init__(self, repo: EquipoRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: AgregarMiembroCommand) -> None:
        await _equipo_propio(self._repo, cmd.equipo_id, cmd.propietario_id)

        usuario_id = await self._repo.usuario_id_por_correo(cmd.correo)
        if usuario_id is None:
            raise NotFound(f"No existe un usuario con el correo {cmd.correo}.")
        if usuario_id == cmd.propietario_id:
            raise ValidationError("No puedes agregarte a ti mismo como miembro.")

        agregado = await self._repo.agregar_miembro(
            equipo_id=cmd.equipo_id,
            usuario_id=usuario_id,
            rol_en_equipo=cmd.rol_en_equipo,
        )
        if not agregado:
            raise Conflict("Esa persona ya está en la plantilla.")


class QuitarMiembro:
    def __init__(self, repo: EquipoRepository) -> None:
        self._repo = repo

    async def execute(
        self, *, equipo_id: int, propietario_id: int, usuario_id: int
    ) -> None:
        await _equipo_propio(self._repo, equipo_id, propietario_id)
        ok = await self._repo.quitar_miembro(
            equipo_id=equipo_id, usuario_id=usuario_id
        )
        if not ok:
            raise NotFound("Esa persona no está en la plantilla.")


class ListarMiembros:
    def __init__(self, repo: EquipoRepository) -> None:
        self._repo = repo

    async def execute(
        self, *, equipo_id: int, propietario_id: int
    ) -> list[Miembro]:
        await _equipo_propio(self._repo, equipo_id, propietario_id)
        return await self._repo.listar_miembros(equipo_id)
