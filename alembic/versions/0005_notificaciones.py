"""Tabla de notificaciones (sin datos sensibles).

Revision ID: 0005_notificaciones
Revises: 0004_encrypt_telefono
Create Date: 2026-06-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_notificaciones"
down_revision: Union[str, None] = "0004_encrypt_telefono"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False
        ),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("titulo", sa.String(150), nullable=False),
        sa.Column("cuerpo", sa.String(500), nullable=False),
        sa.Column("canal", sa.String(20), nullable=False, server_default="in_app"),
        sa.Column(
            "estado", sa.String(20), nullable=False, server_default="pendiente"
        ),
        sa.Column("referencia_tipo", sa.String(40), nullable=True),
        sa.Column("referencia_id", sa.Integer(), nullable=True),
        sa.Column(
            "leida", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("fecha_envio", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "idx_notificaciones_usuario", "notificaciones", ["usuario_id", "leida"]
    )


def downgrade() -> None:
    op.drop_index("idx_notificaciones_usuario", table_name="notificaciones")
    op.drop_table("notificaciones")
