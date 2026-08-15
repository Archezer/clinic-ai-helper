from typing import Literal

from pydantic import BaseModel, Field


class MessengerUser(BaseModel):
    id: str = Field(min_length=1, max_length=255)


class MessengerMessage(BaseModel):
    mid: str = Field(min_length=1, max_length=255)
    text: str | None = Field(default=None, max_length=1000)
    is_echo: bool = False


class MessengerMessagingEvent(BaseModel):
    sender: MessengerUser
    message: MessengerMessage | None = None


class MessengerEntry(BaseModel):
    messaging: list[MessengerMessagingEvent] = Field(default_factory=list)


class MessengerWebhookPayload(BaseModel):
    object: Literal["page"]
    entry: list[MessengerEntry] = Field(default_factory=list)
