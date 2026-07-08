"""material_id/proveedor_id de detalle_presupuesto → VARCHAR.

El microservicio de Proveedores usa IDs de tipo string (UUID). Estas columnas
son referencias LÓGICAS a ese micro (no FK), así que pasan de INTEGER a VARCHAR.

Revision ID: 0010_material_id_varchar
Revises: 0009_grabaciones_local_id
Create Date: 2026-07-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_material_id_varchar"
down_revision: Union[str, None] = "0009_grabaciones_local_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("detalle_presupuesto") as batch:
        batch.alter_column(
            "material_id",
            existing_type=sa.Integer(),
            type_=sa.String(64),
            existing_nullable=True,
            postgresql_using="material_id::varchar",
        )
        batch.alter_column(
            "proveedor_id",
            existing_type=sa.Integer(),
            type_=sa.String(64),
            existing_nullable=True,
            postgresql_using="proveedor_id::varchar",
        )


def downgrade() -> None:
    with op.batch_alter_table("detalle_presupuesto") as batch:
        batch.alter_column(
            "material_id",
            existing_type=sa.String(64),
            type_=sa.Integer(),
            existing_nullable=True,
            postgresql_using="material_id::integer",
        )
        batch.alter_column(
            "proveedor_id",
            existing_type=sa.String(64),
            type_=sa.Integer(),
            existing_nullable=True,
            postgresql_using="proveedor_id::integer",
        )
