"""Router de roles: catálogo público para poblar el selector del registro."""
from fastapi import APIRouter, Depends

from src.features.roles.application.listar_roles import ListarRoles
from src.features.roles.infrastructure.dependencies import get_listar_roles
from src.features.roles.infrastructure.schemas import RolOut

router = APIRouter(tags=["roles"])


@router.get(
    "/roles",
    response_model=list[RolOut],
    summary="Lista los roles disponibles (selector del registro)",
)
async def listar_roles(
    use_case: ListarRoles = Depends(get_listar_roles),
) -> list[RolOut]:
    roles = await use_case.execute()
    return [RolOut(id=r.id, nombre=r.nombre) for r in roles]
