from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ConversationStatus(StrEnum):
    ACTIVE = 'active'
    NEEDS_HUMAN = 'needs_human'
    CLOSED = 'closed'

class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    HUMAN = "human"


class BookingStage(StrEnum):
    IDLE = "idle"
    AWAITING_NAME = "awaiting_name"
    AWAITING_PHONE = "awaiting_phone"
    AWAITING_DATETIME = "awaiting_datetime"

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    external_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(
            ConversationStatus,
            name="conversation_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=ConversationStatus.ACTIVE,
        server_default=ConversationStatus.ACTIVE.value,
    )
    booking_stage: Mapped[BookingStage] = mapped_column(
        Enum(
            BookingStage,
            name="booking_stage",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=BookingStage.IDLE,
        server_default=BookingStage.IDLE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates='conversation',
        cascade='all, delete-orphan'
    )

class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4
    )
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            'conversations.id',
            ondelete='CASCADE'
        ),
        nullable=False,
        index=True
    )
    external_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            name="message_role",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    conversation: Mapped[Conversation] = relationship(
        back_populates="messages",
    )
