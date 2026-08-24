from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.routing import RoutingDecision


class FakeMessengerRequest(BaseModel):
    sender_id: str = Field(default="demo-user", min_length=1, max_length=255)
    text: str = Field(min_length=1, max_length=1000)
    message_id: str = Field(
        default_factory=lambda: f"demo-{uuid4()}",
        min_length=1,
        max_length=255,
    )


class FakeOutgoingMessage(BaseModel):
    recipient_id: str
    text: str


class FakeMessengerResponse(BaseModel):
    decision: RoutingDecision
    outgoing_messages: list[FakeOutgoingMessage]
