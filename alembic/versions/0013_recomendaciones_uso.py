"""recomendaciones_uso: auditoría de recomendaciones de kit y su uso real.

Cada fila es una llamada a POST /recomendaciones/kit. `cotizacion_id` y
`fecha_uso` se completan después, solo si esa recomendación se confirmó en
una cotización real (POST /cotizaciones/kit con recomendacion_id).

Revision ID: 0013_recomendaciones_uso
Revises: 0012_proveedor_distancia
Create Date: 2026-07-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_recomendaciones_uso"
down_revision: Union[str, None] = "0012_proveedor_distancia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recomendaciones_uso",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column(
            "proyecto_id",
            sa.Integer(),
            sa.ForeignKey("proyectos.id"),
            nullable=True,
        ),
        sa.Column("categoria", sa.String(100), nullable=False),
        sa.Column("tipo_kit_recomendado", sa.String(30), nullable=False),
        sa.Column(
            "complementos_recomendados",
            postgresql.JSONB().with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column("metodo_crucetas_recomendado", sa.String(30), nullable=True),
        sa.Column(
            "fecha_solicitud",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "cotizacion_id",
            sa.Integer(),
            sa.ForeignKey("presupuestos.id"),
            nullable=True,
        ),
        sa.Column("fecha_uso", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_recomendaciones_uso_usuario_id", "recomendaciones_uso", ["usuario_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_recomendaciones_uso_usuario_id", table_name="recomendaciones_uso")
    op.drop_table("recomendaciones_uso")
