"""proveedor_distancia en detalle_presupuesto.

La columna se agregó a la migración 0011 después de que esta ya estaba
aplicada en producción, por lo que Alembic nunca volvió a ejecutarla y la
columna nunca se creó en la base real. Esta migración la agrega de forma
idempotente respecto al estado actual de la BD.

Revision ID: 0012_proveedor_distancia
Revises: 0011_proveedor_nombre
Create Date: 2026-07-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_proveedor_distancia"
down_revision: Union[str, None] = "0011_proveedor_nombre"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("detalle_presupuesto") as batch:
        batch.add_column(
            sa.Column("proveedor_distancia", sa.Numeric(9, 2), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("detalle_presupuesto") as batch:
        batch.drop_column("proveedor_distancia")
