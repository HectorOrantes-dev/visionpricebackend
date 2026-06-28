"""Equipos y plantilla (gestión de dirección técnica).

Revision ID: 0008_equipos
Revises: 0007_idempotency
Create Date: 2026-06-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_equipos"
down_revision: Union[str, None] = "0007_idempotency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "equipos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column(
            "propietario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_equipos_propietario", "equipos", ["propietario_id"])

    op.create_table(
        "equipo_miembros",
        sa.Column(
            "equipo_id",
            sa.Integer(),
            sa.ForeignKey("equipos.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            primary_key=True,
        ),
        sa.Column("rol_en_equipo", sa.String(50), nullable=True),
        sa.Column(
            "fecha_asignacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("equipo_miembros")
    op.drop_index("idx_equipos_propietario", table_name="equipos")
    op.drop_table("equipos")
