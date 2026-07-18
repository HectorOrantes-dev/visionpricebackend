"""Router de proyectos (gestión e historial).

Restringido a Permisos.GESTION_PROYECTOS (todos los roles autenticados,
incluido el maestro de obra). Cada operación filtra por dueño (user.id).
"""
from fastapi import APIRouter, Depends, Query, Request, status

from src.features.proyectos.application.gestionar_proyecto import (
    ActualizarProyecto,
    ActualizarProyectoCommand,
    CrearProyecto,
    CrearProyectoCommand,
    ListarProyectos,
    ObtenerProyecto,
)
from src.features.proyectos.infrastructure.dependencies import (
    get_actualizar_proyecto,
    get_crear_proyecto,
    get_listar_proyectos,
    get_obtener_proyecto,
)
from src.features.proyectos.infrastructure.schemas import (
    ActualizarProyectoRequest,
    CrearProyectoRequest,
    ProyectoOut,
)
from src.oauth.dependencies import CurrentUser
from src.oauth.permisos import Permisos
from src.oauth.roles import require_roles
from src.shared.auditoria import Auditor, get_auditor
from src.shared.request_utils import get_client_ip

gestion = require_roles(*Permisos.GESTION_PROYECTOS)

router = APIRouter(prefix="/proyectos", tags=["proyectos"])


@router.post(
    "",
    response_model=ProyectoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un proyecto",
)
async def crear(
    body: CrearProyectoRequest,
    request: Request,
    user: CurrentUser = Depends(gestion),
    use_case: CrearProyecto = Depends(get_crear_proyecto),
    auditor: Auditor = Depends(get_auditor),
) -> ProyectoOut:
    proyecto = await use_case.execute(
        CrearProyectoCommand(
            usuario_id=user.id,
            nombre=body.nombre,
            direccion=body.direccion,
            latitud=body.latitud,
            longitud=body.longitud,
        )
    )
    await auditor.registrar(
        usuario_id=user.id,
        accion="proyecto_creado",
        tabla_afectada="proyectos",
        registro_id=proyecto.id,
        ip_origen=get_client_ip(request),
    )
    return ProyectoOut(**_out(proyecto))


@router.get(
    "",
    response_model=list[ProyectoOut],
    summary="Historial de mis proyectos (opcional ?estado=)",
)
async def listar(
    estado: str | None = Query(default=None),
    user: CurrentUser = Depends(gestion),
    use_case: ListarProyectos = Depends(get_listar_proyectos),
) -> list[ProyectoOut]:
    proyectos = await use_case.execute(user.id, estado)
    return [ProyectoOut(**_out(p)) for p in proyectos]


@router.get(
    "/{proyecto_id}",
    response_model=ProyectoOut,
    summary="Detalle de un proyecto",
)
async def obtener(
    proyecto_id: int,
    user: CurrentUser = Depends(gestion),
    use_case: ObtenerProyecto = Depends(get_obtener_proyecto),
) -> ProyectoOut:
    proyecto = await use_case.execute(proyecto_id, user.id)
    return ProyectoOut(**_out(proyecto))


@router.patch(
    "/{proyecto_id}",
    response_model=ProyectoOut,
    summary="Actualizar un proyecto (datos o estado)",
)
async def actualizar(
    proyecto_id: int,
    body: ActualizarProyectoRequest,
    user: CurrentUser = Depends(gestion),
    use_case: ActualizarProyecto = Depends(get_actualizar_proyecto),
) -> ProyectoOut:
    proyecto = await use_case.execute(
        ActualizarProyectoCommand(
            proyecto_id=proyecto_id,
            usuario_id=user.id,
            cambios=body.model_dump(exclude_unset=True),
        )
    )
    return ProyectoOut(**_out(proyecto))


def _out(p) -> dict:
    return {
        "id": p.id,
        "nombre": p.nombre,
        "direccion": p.direccion,
        "latitud": p.latitud,
        "longitud": p.longitud,
        "estado": p.estado,
        "fecha_creacion": p.fecha_creacion,
        "total_presupuestos": p.total_presupuestos,
        "es_dueno": p.es_dueno,
    }

