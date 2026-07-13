"""proveedor_nombre en detalle_presupuesto.

Se persiste el nombre del proveedor al crear la cotización (ya llega del
microservicio de Proveedores vía ProductoCercano, antes se descartaba). Sirve
para agrupar por proveedor en el PDF combinado de un proyecto sin tener que
re-consultar al micro al generar el documento.

Revision ID: 0011_proveedor_nombre
Revises: 0010_material_id_varchar
Create Date: 2026-07-12
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_proveedor_nombre"
down_revision: Union[str, None] = "0010_material_id_varchar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("detalle_presupuesto") as batch:
        batch.add_column(
            sa.Column("proveedor_nombre", sa.String(255), nullable=True)
        )
        batch.add_column(
            sa.Column("proveedor_distancia", sa.Numeric(9, 2), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("detalle_presupuesto") as batch:
        batch.drop_column("proveedor_nombre")
        batch.drop_column("proveedor_distancia")
