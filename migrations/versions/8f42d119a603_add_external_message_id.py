"""add external message id

Revision ID: 8f42d119a603
Revises: 2305a1d34062
Create Date: 2026-08-15

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "8f42d119a603"
down_revision: str | Sequence[str] | None = "2305a1d34062"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column(
            "external_message_id",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_messages_external_message_id",
        "messages",
        ["external_message_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_messages_external_message_id",
        "messages",
        type_="unique",
    )
    op.drop_column("messages", "external_message_id")
