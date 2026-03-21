"""Migración inicial: crea las tablas conversations y messages.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Tabla conversations ──────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id",         sa.Integer(),     nullable=False),
        sa.Column("title",      sa.String(255),   nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_id", "conversations", ["id"], unique=False)

    # ── Tabla messages ───────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id",              sa.Integer(),    nullable=False),
        sa.Column("conversation_id", sa.Integer(),    nullable=False),
        sa.Column("role",            sa.String(50),   nullable=False),
        sa.Column("content",         sa.Text(),       nullable=False),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_id",              "messages", ["id"],              unique=False)
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_index("ix_messages_id",              table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_id", table_name="conversations")
    op.drop_table("conversations")
