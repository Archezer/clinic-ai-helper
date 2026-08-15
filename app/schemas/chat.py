from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=1000,
    )


class ProcessMessageRequest(ChatRequest):
    channel: Literal["messenger"]
    external_user_id: str = Field(
        min_length=1,
        max_length=255,
    )
    external_message_id: str = Field(
        min_length=1,
        max_length=255,
    )
