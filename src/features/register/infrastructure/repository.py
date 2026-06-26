"""Adaptador SQLAlchemy del repositorio de registro."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.register.domain.entities import NewUser, RegisteredUser
from src.features.register.domain.ports import RegisterUserRepository
from src.shared.models import Rol, Usuario


class SqlAlchemyRegisterRepository(RegisterUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def email_exists(self, correo: str) -> bool:
        result = await self._session.execute(
            select(Usuario.id).where(Usuario.correo == correo)
        )
        return result.scalar_one_or_none() is not None

    async def get_role_id(self, nombre: str) -> int | None:
        result = await self._session.execute(
            select(Rol.id).where(Rol.nombre == nombre)
        )
        return result.scalar_one_or_none()

    async def create(self, new_user: NewUser) -> RegisteredUser:
        usuario = Usuario(
            nombre=new_user.nombre,
            correo=new_user.correo,
            contrasena_hash=new_user.contrasena_hash,
            telefono=new_user.telefono,
            rol_id=new_user.rol_id,
        )
        self._session.add(usuario)
        await self._session.commit()
        await self._session.refresh(usuario, attribute_names=["rol"])

        return RegisteredUser(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            telefono=usuario.telefono,
            rol_id=usuario.rol_id,
            rol=usuario.rol.nombre,
            activo=usuario.activo,
            fecha_registro=usuario.fecha_registro,
        )
