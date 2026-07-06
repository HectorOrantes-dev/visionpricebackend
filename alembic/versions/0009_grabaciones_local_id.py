"""Idempotencia de grabaciones: local_id (cola offline).

Revision ID: 0009_grabaciones_local_id
Revises: 0008_equipos
Create Date: 2026-07-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_grabaciones_local_id"
down_revision: Union[str, None] = "0008_equipos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "grabaciones_audio",
        sa.Column("local_id", sa.String(64), nullable=True),
    )
    # Índice único (funciona en SQLite y Postgres, sin recrear la tabla).
    op.create_index(
        "uq_grabaciones_usuario_local",
        "grabaciones_audio",
        ["usuario_id", "local_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_grabaciones_usuario_local", table_name="grabaciones_audio")
    op.drop_column("grabaciones_audio", "local_id")
