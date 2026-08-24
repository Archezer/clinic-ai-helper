from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.routing import RoutingDecision


class WebDemoChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str = Field(
        default_factory=lambda: f"web-demo-{uuid4()}",
        min_length=1,
        max_length=255,
    )


class WebDemoEvent(BaseModel):
    type: str
    value: str


class WebDemoChatResponse(BaseModel):
    session_id: str
    reply: str
    decision: RoutingDecision
    events: list[WebDemoEvent]
