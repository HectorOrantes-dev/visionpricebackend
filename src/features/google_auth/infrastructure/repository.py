"""Adaptador SQLAlchemy del repositorio de google_auth."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.features.google_auth.domain.entities import GoogleUser
from src.features.google_auth.domain.ports import GoogleUserRepository
from src.shared.errors import NotFound
from src.shared.models import Rol, Usuario


class SqlAlchemyGoogleRepository(GoogleUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_correo(self, correo: str) -> GoogleUser | None:
        result = await self._session.execute(
            select(Usuario)
            .options(joinedload(Usuario.rol))
            .where(Usuario.correo == correo)
        )
        usuario = result.scalar_one_or_none()
        if usuario is None:
            return None
        return GoogleUser(
            id=usuario.id,
            correo=usuario.correo,
            rol=usuario.rol.nombre,
            activo=usuario.activo,
            google_sub=usuario.google_sub,
        )

    async def get_role_id(self, nombre: str) -> int | None:
        result = await self._session.execute(
            select(Rol.id).where(Rol.nombre == nombre)
        )
        return result.scalar_one_or_none()

    async def crear_google(
        self, *, nombre: str, correo: str, rol_id: int, google_sub: str
    ) -> GoogleUser:
        usuario = Usuario(
            nombre=nombre,
            correo=correo,
            contrasena_hash=None,
            rol_id=rol_id,
            proveedor_auth="google",
            google_sub=google_sub,
        )
        self._session.add(usuario)
        await self._session.commit()
        await self._session.refresh(usuario, attribute_names=["rol"])
        return GoogleUser(
            id=usuario.id,
            correo=usuario.correo,
            rol=usuario.rol.nombre,
            activo=usuario.activo,
            google_sub=usuario.google_sub,
        )

    async def vincular_google(self, usuario_id: int, google_sub: str) -> None:
        usuario = await self._session.get(Usuario, usuario_id)
        if usuario is None:
            raise NotFound("Usuario no encontrado.")
        if usuario.google_sub is None:
            usuario.google_sub = google_sub
            if usuario.proveedor_auth == "local":
                # cuenta local que ahora también usa Google
                usuario.proveedor_auth = "google"
            await self._session.commit()
