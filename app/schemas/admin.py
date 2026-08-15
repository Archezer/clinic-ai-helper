from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import AppointmentStatus, ConversationStatus, MessageRole


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    channel: str
    external_user_id: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime


class MessageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    content: str
    created_at: datetime


class HumanReplyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class AdminActionResponse(BaseModel):
    status: str


class FaqCreateRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    answer: str = Field(min_length=1, max_length=4000)
    keywords: str = Field(default="", max_length=1000)


class FaqView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    answer: str
    keywords: str
    is_active: bool


class AppointmentQueueItem(BaseModel):
    id: UUID
    patient_id: UUID
    conversation_id: UUID
    patient_name: str | None
    patient_phone: str | None
    requested_time_text: str
    status: AppointmentStatus
    created_at: datetime


class AppointmentStatusRequest(BaseModel):
    status: AppointmentStatus
