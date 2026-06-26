"""Callbacks ML/Pagos + desafíos 2FA.

- usuarios: + plan_activo, + vigencia_hasta (entitlement cacheado de Pagos)
- grabaciones_audio: + object_storage_key (referencia al audio en object storage)
- nueva tabla desafios_2fa (estado de los desafíos de login)

Revision ID: 0002_callbacks_2fa
Revises: 0001_initial
Create Date: 2026-06-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_callbacks_2fa"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios", sa.Column("plan_activo", sa.String(50), nullable=True)
    )
    op.add_column(
        "usuarios", sa.Column("vigencia_hasta", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "grabaciones_audio",
        sa.Column("object_storage_key", sa.String(512), nullable=True),
    )

    op.create_table(
        "desafios_2fa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True
        ),
        sa.Column("correo", sa.String(150), nullable=False),
        sa.Column(
            "proposito", sa.String(20), nullable=False, server_default="login"
        ),
        sa.Column(
            "estado", sa.String(20), nullable=False, server_default="pendiente"
        ),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip_origen", sa.String(45), nullable=True),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("fecha_verificacion", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_desafios_2fa_correo", "desafios_2fa", ["correo"])


def downgrade() -> None:
    op.drop_index("idx_desafios_2fa_correo", table_name="desafios_2fa")
    op.drop_table("desafios_2fa")
    op.drop_column("grabaciones_audio", "object_storage_key")
    op.drop_column("usuarios", "vigencia_hasta")
    op.drop_column("usuarios", "plan_activo")
