"""Router de membresía e invitaciones de proyectos.

Todos los endpoints viven bajo /proyectos (mismo prefijo que el router base).
Se monta en main.py con el mismo prefix /api/v1.
"""
from fastapi import APIRouter, Depends, Request, status

from src.features.proyectos.application.membresia import (
    CrearInvitacion,
    CrearInvitacionCommand,
    ListarInvitaciones,
    ListarInvitacionesCommand,
    ListarMiembros,
    ListarMiembrosCommand,
    QuitarMiembro,
    QuitarMiembroCommand,
    RevocarInvitacion,
    RevocarInvitacionCommand,
    UnirseAProyecto,
    UnirseAProyectoCommand,
)
from src.features.proyectos.infrastructure.membresia_schemas import (
    CrearInvitacionRequest,
    InvitacionOut,
    MiembroOut,
    OkOut,
    UnirseRequest,
)
from src.features.proyectos.infrastructure.dependencies import (
    get_crear_invitacion,
    get_listar_invitaciones,
    get_listar_miembros,
    get_quitar_miembro,
    get_revocar_invitacion,
    get_unirse_a_proyecto,
)
from src.oauth.dependencies import CurrentUser, get_current_user
from src.shared.auditoria import Auditor, get_auditor
from src.shared.rate_limit import rate_limit
from src.shared.request_utils import get_client_ip

router = APIRouter(prefix="/proyectos", tags=["proyectos-membresia"])

# Rate-limit: el dueño puede crear máx. 5 invitaciones cada 60 s.
_limite_inv = rate_limit(5, 60)


# ---------------------------------------------------------------------------
# Crear invitación (dueño)
# ---------------------------------------------------------------------------


@router.post(
    "/{proyecto_id}/invitaciones",
    response_model=InvitacionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generar código de invitación multiuso (3 días de vigencia)",
)
async def crear_invitacion(
    proyecto_id: int,
    body: CrearInvitacionRequest,
    request: Request,
    user: CurrentUser = Depends(_limite_inv),
    use_case: CrearInvitacion = Depends(get_crear_invitacion),
    auditor: Auditor = Depends(get_auditor),
) -> InvitacionOut:
    inv = await use_case.execute(
        CrearInvitacionCommand(
            proyecto_id=proyecto_id,
            invitado_por=user.id,
            rol_en_proyecto=body.rol_en_proyecto,
            correos=[str(c) for c in body.correos],
        )
    )
    await auditor.registrar(
        usuario_id=user.id,
        accion="invitacion_creada",
        tabla_afectada="proyecto_invitaciones",
        registro_id=inv.id,
        detalles={"proyecto_id": proyecto_id, "rol": inv.rol_en_proyecto},
        ip_origen=get_client_ip(request),
    )
    return InvitacionOut(
        id=inv.id,
        proyecto_id=inv.proyecto_id,
        codigo=inv.codigo,
        rol_en_proyecto=inv.rol_en_proyecto,
        estado=inv.estado,
        usos=inv.usos,
        fecha_creacion=inv.fecha_creacion,
        fecha_expiracion=inv.fecha_expiracion,
    )


# ---------------------------------------------------------------------------
# Unirse a proyecto (cualquier usuario autenticado)
# ---------------------------------------------------------------------------


@router.post(
    "/unirse",
    response_model=MiembroOut,
    status_code=status.HTTP_200_OK,
    summary="Unirse a un proyecto con un código de invitación",
)
async def unirse(
    body: UnirseRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    use_case: UnirseAProyecto = Depends(get_unirse_a_proyecto),
    auditor: Auditor = Depends(get_auditor),
) -> MiembroOut:
    miembro = await use_case.execute(
        UnirseAProyectoCommand(codigo=body.codigo, usuario_id=user.id)
    )
    await auditor.registrar(
        usuario_id=user.id,
        accion="proyecto_unido",
        tabla_afectada="proyecto_colaboradores",
        registro_id=miembro.proyecto_id,
        detalles={"proyecto_id": miembro.proyecto_id, "rol": miembro.rol_en_proyecto},
        ip_origen=get_client_ip(request),
    )
    return MiembroOut(
        usuario_id=miembro.usuario_id,
        nombre=miembro.nombre,
        correo=miembro.correo,
        rol_en_proyecto=miembro.rol_en_proyecto,
        fecha_asignacion=miembro.fecha_asignacion,
    )


# ---------------------------------------------------------------------------
# Listar miembros (miembro O dueño)
# ---------------------------------------------------------------------------


@router.get(
    "/{proyecto_id}/miembros",
    response_model=list[MiembroOut],
    summary="Listar miembros del proyecto",
)
async def listar_miembros(
    proyecto_id: int,
    user: CurrentUser = Depends(get_current_user),
    use_case: ListarMiembros = Depends(get_listar_miembros),
) -> list[MiembroOut]:
    miembros = await use_case.execute(
        ListarMiembrosCommand(proyecto_id=proyecto_id, solicitante_id=user.id)
    )
    return [
        MiembroOut(
            usuario_id=m.usuario_id,
            nombre=m.nombre,
            correo=m.correo,
            rol_en_proyecto=m.rol_en_proyecto,
            fecha_asignacion=m.fecha_asignacion,
        )
        for m in miembros
    ]


# ---------------------------------------------------------------------------
# Quitar miembro (dueño)
# ---------------------------------------------------------------------------


@router.delete(
    "/{proyecto_id}/miembros/{usuario_id}",
    response_model=OkOut,
    summary="Eliminar a un miembro del proyecto (solo dueño)",
)
async def quitar_miembro(
    proyecto_id: int,
    usuario_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    use_case: QuitarMiembro = Depends(get_quitar_miembro),
    auditor: Auditor = Depends(get_auditor),
) -> OkOut:
    await use_case.execute(
        QuitarMiembroCommand(
            proyecto_id=proyecto_id,
            solicitante_id=user.id,
            usuario_id=usuario_id,
        )
    )
    await auditor.registrar(
        usuario_id=user.id,
        accion="miembro_removido",
        tabla_afectada="proyecto_colaboradores",
        registro_id=proyecto_id,
        detalles={"proyecto_id": proyecto_id, "usuario_id_removido": usuario_id},
        ip_origen=get_client_ip(request),
    )
    return OkOut()


# ---------------------------------------------------------------------------
# Listar invitaciones activas (dueño)
# ---------------------------------------------------------------------------


@router.get(
    "/{proyecto_id}/invitaciones",
    response_model=list[InvitacionOut],
    summary="Ver los códigos de invitación activos del proyecto (solo dueño)",
)
async def listar_invitaciones(
    proyecto_id: int,
    user: CurrentUser = Depends(get_current_user),
    use_case: ListarInvitaciones = Depends(get_listar_invitaciones),
) -> list[InvitacionOut]:
    invitaciones = await use_case.execute(
        ListarInvitacionesCommand(proyecto_id=proyecto_id, solicitante_id=user.id)
    )
    return [
        InvitacionOut(
            id=inv.id,
            proyecto_id=inv.proyecto_id,
            codigo=inv.codigo,
            rol_en_proyecto=inv.rol_en_proyecto,
            estado=inv.estado,
            usos=inv.usos,
            fecha_creacion=inv.fecha_creacion,
            fecha_expiracion=inv.fecha_expiracion,
        )
        for inv in invitaciones
    ]


# ---------------------------------------------------------------------------
# Revocar invitación (dueño)
# ---------------------------------------------------------------------------


@router.post(
    "/{proyecto_id}/invitaciones/{invitacion_id}/revocar",
    response_model=OkOut,
    summary="Revocar un código de invitación antes de que expire (solo dueño)",
)
async def revocar_invitacion(
    proyecto_id: int,
    invitacion_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    use_case: RevocarInvitacion = Depends(get_revocar_invitacion),
    auditor: Auditor = Depends(get_auditor),
) -> OkOut:
    await use_case.execute(
        RevocarInvitacionCommand(
            proyecto_id=proyecto_id,
            invitacion_id=invitacion_id,
            solicitante_id=user.id,
        )
    )
    await auditor.registrar(
        usuario_id=user.id,
        accion="invitacion_revocada",
        tabla_afectada="proyecto_invitaciones",
        registro_id=invitacion_id,
        detalles={"proyecto_id": proyecto_id},
        ip_origen=get_client_ip(request),
    )
    return OkOut()
