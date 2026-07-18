"""Casos de uso de membresía e invitaciones de proyectos.

Contiene 6 use cases:
  - CrearInvitacion    → dueño genera código multiuso (3 días).
  - UnirseAProyecto    → cualquier usuario auth usa el código.
  - ListarMiembros     → miembros/dueño ven la plantilla.
  - QuitarMiembro      → dueño elimina a un colaborador.
  - ListarInvitaciones → dueño ve los códigos activos.
  - RevocarInvitacion  → dueño mata un código antes de expirar.
"""
import logging
import secrets
import string
from dataclasses import dataclass, field
from datetime import timedelta

from src.features.proyectos.domain.entities import Invitacion, Miembro
from src.features.proyectos.domain.ports import (
    CorreoPort,
    InvitacionRepository,
    MembresiaRepository,
)
from src.shared.errors import Conflict, Forbidden, NotFound, ValidationError
from src.shared.timeutils import utcnow

_log = logging.getLogger("proyectos.membresia")

_CHARS = string.ascii_uppercase + string.digits
_CODIGO_LEN = 10

RolEnProyecto = str  # cualquier string; validación en el schema Pydantic


def _generar_codigo() -> str:
    """Genera un código alfanumérico de 10 caracteres (≈ 36^10 combinaciones)."""
    return "".join(secrets.choice(_CHARS) for _ in range(_CODIGO_LEN))


# ---------------------------------------------------------------------------
# Crear Invitación
# ---------------------------------------------------------------------------


@dataclass
class CrearInvitacionCommand:
    proyecto_id: int
    invitado_por: int  # usuario_id del dueño
    rol_en_proyecto: str
    correos: list[str] = field(default_factory=list)
    dias_vigencia: int = 3


class CrearInvitacion:
    def __init__(
        self,
        membresia_repo: MembresiaRepository,
        inv_repo: InvitacionRepository,
        correo_port: CorreoPort,
    ) -> None:
        self._mem = membresia_repo
        self._inv = inv_repo
        self._correo = correo_port

    async def execute(self, cmd: CrearInvitacionCommand) -> Invitacion:
        # Solo el dueño puede invitar.
        if not await self._mem.es_dueno(cmd.proyecto_id, cmd.invitado_por):
            raise Forbidden("Solo el dueño del proyecto puede crear invitaciones.")

        if not cmd.rol_en_proyecto.strip():
            raise ValidationError("El rol_en_proyecto es obligatorio.")

        # Generar código único (reintento si colisión).
        for _ in range(10):
            codigo = _generar_codigo()
            if not await self._inv.codigo_existe(codigo):
                break
        else:
            raise ValidationError("No se pudo generar un código único. Intenta de nuevo.")

        ahora = utcnow()
        inv = Invitacion(
            id=0,  # lo asigna la BD
            proyecto_id=cmd.proyecto_id,
            codigo=codigo,
            rol_en_proyecto=cmd.rol_en_proyecto,
            estado="activa",
            usos=0,
            invitado_por=cmd.invitado_por,
            fecha_creacion=ahora,
            fecha_expiracion=ahora + timedelta(days=cmd.dias_vigencia),
        )
        inv = await self._inv.crear(inv)

        # Enviar correos si se especificaron (falla silenciosa por diseño).
        for correo in cmd.correos:
            try:
                await self._correo.enviar(
                    correo=correo,
                    asunto="Te invitaron a un proyecto en VisionPrice",
                    cuerpo=(
                        f"Usa el siguiente código para unirte al proyecto:\n\n"
                        f"  {codigo}\n\n"
                        f"Válido por {cmd.dias_vigencia} días. "
                        f"Ingresa desde la app con POST /api/v1/proyectos/unirse."
                    ),
                )
            except Exception as exc:  # noqa: BLE001
                _log.warning("No se pudo enviar correo a %s: %s", correo, exc)

        return inv


# ---------------------------------------------------------------------------
# Unirse a Proyecto
# ---------------------------------------------------------------------------


@dataclass
class UnirseAProyectoCommand:
    codigo: str
    usuario_id: int


class UnirseAProyecto:
    def __init__(
        self,
        membresia_repo: MembresiaRepository,
        inv_repo: InvitacionRepository,
    ) -> None:
        self._mem = membresia_repo
        self._inv = inv_repo

    async def execute(self, cmd: UnirseAProyectoCommand) -> Miembro:
        inv = await self._inv.obtener_por_codigo(cmd.codigo)
        if inv is None:
            raise NotFound("Código de invitación no encontrado.")

        if inv.estado != "activa":
            raise Conflict(f"El código está {inv.estado}.")

        ahora = utcnow()
        if ahora > inv.fecha_expiracion:
            raise Conflict("El código de invitación ha expirado.")

        # El dueño no puede unirse como colaborador de su propio proyecto.
        if await self._mem.es_dueno(inv.proyecto_id, cmd.usuario_id):
            raise Conflict("Ya eres el dueño de este proyecto.")

        # Idempotente: si ya es miembro, avisa sin duplicar.
        if await self._mem.es_miembro(inv.proyecto_id, cmd.usuario_id):
            raise Conflict("Ya eres miembro de este proyecto.")

        miembro = await self._mem.agregar(
            proyecto_id=inv.proyecto_id,
            usuario_id=cmd.usuario_id,
            rol=inv.rol_en_proyecto,
        )
        await self._inv.incrementar_usos(inv.id)
        return miembro


# ---------------------------------------------------------------------------
# Listar Miembros
# ---------------------------------------------------------------------------


@dataclass
class ListarMiembrosCommand:
    proyecto_id: int
    solicitante_id: int


class ListarMiembros:
    def __init__(self, membresia_repo: MembresiaRepository) -> None:
        self._mem = membresia_repo

    async def execute(self, cmd: ListarMiembrosCommand) -> list[Miembro]:
        if not await self._mem.puede_acceder(cmd.proyecto_id, cmd.solicitante_id):
            raise Forbidden("No tienes acceso a este proyecto.")
        return await self._mem.listar(cmd.proyecto_id)


# ---------------------------------------------------------------------------
# Quitar Miembro
# ---------------------------------------------------------------------------


@dataclass
class QuitarMiembroCommand:
    proyecto_id: int
    solicitante_id: int
    usuario_id: int  # el que se quita


class QuitarMiembro:
    def __init__(self, membresia_repo: MembresiaRepository) -> None:
        self._mem = membresia_repo

    async def execute(self, cmd: QuitarMiembroCommand) -> None:
        if not await self._mem.es_dueno(cmd.proyecto_id, cmd.solicitante_id):
            raise Forbidden("Solo el dueño puede eliminar miembros.")
        if cmd.solicitante_id == cmd.usuario_id:
            raise ValidationError("El dueño no puede eliminarse a sí mismo.")
        removed = await self._mem.quitar(cmd.proyecto_id, cmd.usuario_id)
        if not removed:
            raise NotFound("El usuario no es miembro de este proyecto.")


# ---------------------------------------------------------------------------
# Listar Invitaciones
# ---------------------------------------------------------------------------


@dataclass
class ListarInvitacionesCommand:
    proyecto_id: int
    solicitante_id: int


class ListarInvitaciones:
    def __init__(
        self,
        membresia_repo: MembresiaRepository,
        inv_repo: InvitacionRepository,
    ) -> None:
        self._mem = membresia_repo
        self._inv = inv_repo

    async def execute(self, cmd: ListarInvitacionesCommand) -> list[Invitacion]:
        if not await self._mem.es_dueno(cmd.proyecto_id, cmd.solicitante_id):
            raise Forbidden("Solo el dueño puede ver los códigos de invitación.")
        return await self._inv.listar_activas_de_proyecto(cmd.proyecto_id)


# ---------------------------------------------------------------------------
# Revocar Invitación
# ---------------------------------------------------------------------------


@dataclass
class RevocarInvitacionCommand:
    proyecto_id: int
    invitacion_id: int
    solicitante_id: int


class RevocarInvitacion:
    def __init__(
        self,
        membresia_repo: MembresiaRepository,
        inv_repo: InvitacionRepository,
    ) -> None:
        self._mem = membresia_repo
        self._inv = inv_repo

    async def execute(self, cmd: RevocarInvitacionCommand) -> None:
        if not await self._mem.es_dueno(cmd.proyecto_id, cmd.solicitante_id):
            raise Forbidden("Solo el dueño puede revocar invitaciones.")
        revocada = await self._inv.revocar(cmd.invitacion_id)
        if not revocada:
            raise NotFound("Invitación no encontrada.")
