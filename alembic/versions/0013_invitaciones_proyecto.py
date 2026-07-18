"""Membresía unificada: tabla proyecto_invitaciones (códigos de invitación).

PENDIENTE ⚠️: drop de equipos / equipo_miembros se hará en 0014 una vez
confirmado que las tablas están vacías en producción.

Revision ID: 0013_invitaciones_proyecto
Revises: 0012_proveedor_distancia
Create Date: 2026-07-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_invitaciones_proyecto"
down_revision: Union[str, None] = "0012_proveedor_distancia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "proyecto_invitaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "proyecto_id",
            sa.Integer(),
            sa.ForeignKey("proyectos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("codigo", sa.String(16), nullable=False, unique=True),
        sa.Column("rol_en_proyecto", sa.String(50), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="activa",
        ),  # activa | expirada | revocada
        sa.Column(
            "usos",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "invitado_por",
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
        sa.Column("fecha_expiracion", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "idx_invitaciones_codigo", "proyecto_invitaciones", ["codigo"]
    )
    op.create_index(
        "idx_invitaciones_proyecto", "proyecto_invitaciones", ["proyecto_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_invitaciones_proyecto", table_name="proyecto_invitaciones")
    op.drop_index("idx_invitaciones_codigo", table_name="proyecto_invitaciones")
    op.drop_table("proyecto_invitaciones")
