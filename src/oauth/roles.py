"""Autorización por rol (RBAC) a nivel de ruta.

El rol viaja en el JWT (claim `rol`). `require_roles(...)` es una dependencia
que exige que el usuario tenga uno de los roles permitidos; si no, 403.

Uso en una ruta:
    @router.post("/cotizaciones")
    async def crear(
        user: CurrentUser = Depends(require_roles("contratista", "arquitecto")),
    ):
        ...
"""
from fastapi import Depends

from src.oauth.dependencies import CurrentUser, get_current_user
from src.shared.errors import Forbidden


def require_roles(*roles: str):
    async def _dep(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if user.rol not in roles:
            raise Forbidden(
                "No tienes permiso para esta acción.",
                details={"rol": user.rol, "permitidos": list(roles)},
            )
        return user

    return _dep
