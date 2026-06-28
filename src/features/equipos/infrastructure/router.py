"""Router de equipos / plantilla.

Solo arquitecto e ingeniero civil (Permisos.GESTION_EQUIPOS). Además, cada
operación valida que el equipo pertenezca al usuario (en el caso de uso).
"""
from fastapi import APIRouter, Depends, status

from src.features.equipos.application.gestionar_equipo import (
    AgregarMiembro,
    AgregarMiembroCommand,
    CrearEquipo,
    ListarMiembros,
    ListarMisEquipos,
    QuitarMiembro,
)
from src.features.equipos.infrastructure.dependencies import (
    get_agregar_miembro,
    get_crear_equipo,
    get_listar_equipos,
    get_listar_miembros,
    get_quitar_miembro,
)
from src.features.equipos.infrastructure.schemas import (
    AgregarMiembroRequest,
    CrearEquipoRequest,
    EquipoOut,
    MiembroOut,
    OkOut,
)
from src.oauth.dependencies import CurrentUser
from src.oauth.permisos import Permisos
from src.oauth.roles import require_roles

# Toda la feature exige rol arquitecto / ingeniero civil.
direccion_tecnica = require_roles(*Permisos.GESTION_EQUIPOS)

router = APIRouter(prefix="/equipos", tags=["equipos"])


@router.post(
    "",
    response_model=EquipoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un equipo (arquitecto / ingeniero civil)",
)
async def crear(
    body: CrearEquipoRequest,
    user: CurrentUser = Depends(direccion_tecnica),
    use_case: CrearEquipo = Depends(get_crear_equipo),
) -> EquipoOut:
    equipo = await use_case.execute(nombre=body.nombre, propietario_id=user.id)
    return EquipoOut(**equipo.__dict__)


@router.get(
    "",
    response_model=list[EquipoOut],
    summary="Listar mis equipos",
)
async def listar(
    user: CurrentUser = Depends(direccion_tecnica),
    use_case: ListarMisEquipos = Depends(get_listar_equipos),
) -> list[EquipoOut]:
    return [EquipoOut(**e.__dict__) for e in await use_case.execute(user.id)]


@router.post(
    "/{equipo_id}/miembros",
    response_model=OkOut,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir una persona a la plantilla (por correo)",
)
async def agregar_miembro(
    equipo_id: int,
    body: AgregarMiembroRequest,
    user: CurrentUser = Depends(direccion_tecnica),
    use_case: AgregarMiembro = Depends(get_agregar_miembro),
) -> OkOut:
    await use_case.execute(
        AgregarMiembroCommand(
            equipo_id=equipo_id,
            propietario_id=user.id,
            correo=body.correo,
            rol_en_equipo=body.rol_en_equipo,
        )
    )
    return OkOut()


@router.get(
    "/{equipo_id}/miembros",
    response_model=list[MiembroOut],
    summary="Listar la plantilla de un equipo",
)
async def listar_miembros(
    equipo_id: int,
    user: CurrentUser = Depends(direccion_tecnica),
    use_case: ListarMiembros = Depends(get_listar_miembros),
) -> list[MiembroOut]:
    miembros = await use_case.execute(equipo_id=equipo_id, propietario_id=user.id)
    return [MiembroOut(**m.__dict__) for m in miembros]


@router.delete(
    "/{equipo_id}/miembros/{usuario_id}",
    response_model=OkOut,
    summary="Quitar a una persona de la plantilla",
)
async def quitar_miembro(
    equipo_id: int,
    usuario_id: int,
    user: CurrentUser = Depends(direccion_tecnica),
    use_case: QuitarMiembro = Depends(get_quitar_miembro),
) -> OkOut:
    await use_case.execute(
        equipo_id=equipo_id, propietario_id=user.id, usuario_id=usuario_id
    )
    return OkOut()
