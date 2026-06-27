"""Tabla de dispositivos (device tokens de FCM).

Revision ID: 0006_dispositivos
Revises: 0005_notificaciones
Create Date: 2026-06-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_dispositivos"
down_revision: Union[str, None] = "0005_notificaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dispositivos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False
        ),
        sa.Column("token", sa.String(512), nullable=False, unique=True),
        sa.Column("plataforma", sa.String(20), nullable=False),
        sa.Column(
            "activo", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "fecha_registro",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "fecha_actualizacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_dispositivos_usuario", "dispositivos", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("idx_dispositivos_usuario", table_name="dispositivos")
    op.drop_table("dispositivos")
