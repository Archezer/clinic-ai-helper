"""add booking and faq

Revision ID: c4a82e19d615
Revises: 8f42d119a603
Create Date: 2026-08-15

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c4a82e19d615"
down_revision: str | Sequence[str] | None = "8f42d119a603"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    booking_stage = postgresql.ENUM(
        "idle",
        "awaiting_name",
        "awaiting_phone",
        "awaiting_datetime",
        name="booking_stage",
        create_type=False,
    )
    appointment_status = postgresql.ENUM(
        "requested",
        "confirmed",
        "cancelled",
        name="appointment_status",
        create_type=False,
    )
    booking_stage.create(op.get_bind(), checkfirst=True)
    appointment_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "conversations",
        sa.Column(
            "booking_stage",
            booking_stage,
            server_default="idle",
            nullable=False,
        ),
    )
    op.create_table(
        "patients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("external_user_id", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "channel",
            "external_user_id",
            name="uq_patients_channel_external_user",
        ),
    )
    op.create_table(
        "appointments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("requested_time_text", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            appointment_status,
            server_default="requested",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_appointments_conversation_id",
        "appointments",
        ["conversation_id"],
    )
    op.create_index(
        "ix_appointments_patient_id",
        "appointments",
        ["patient_id"],
    )
    op.create_table(
        "faq_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question", sa.String(length=500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("faq_entries")
    op.drop_index("ix_appointments_patient_id", table_name="appointments")
    op.drop_index(
        "ix_appointments_conversation_id",
        table_name="appointments",
    )
    op.drop_table("appointments")
    op.drop_table("patients")
    op.drop_column("conversations", "booking_stage")
    sa.Enum(name="appointment_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="booking_stage").drop(op.get_bind(), checkfirst=True)
