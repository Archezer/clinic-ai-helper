from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.dependencies import FakeMessengerSession, get_fake_messenger_session
from app.schemas.web_demo import (
    WebDemoChatRequest,
    WebDemoChatResponse,
    WebDemoEvent,
)


router = APIRouter(prefix="/api/demo", tags=["web-demo"])

DemoSessionDependency = Annotated[
    FakeMessengerSession,
    Depends(get_fake_messenger_session),
]


@router.post("/chat", response_model=WebDemoChatResponse)
async def demo_chat(
    payload: WebDemoChatRequest,
    demo_session: DemoSessionDependency,
) -> WebDemoChatResponse:
    decision = await demo_session.chat_service.process_message(
        message=payload.message,
        channel="web-demo",
        external_user_id=payload.session_id,
        external_message_id=f"{payload.session_id}:{uuid4()}",
    )
    outgoing = demo_session.message_sender.messages[-1:]
    reply = outgoing[0].text if outgoing else "No response was generated."

    events = [
        WebDemoEvent(type="intent", value=decision.intent.value),
        WebDemoEvent(type="action", value=decision.action.value),
        WebDemoEvent(
            type="human_handoff",
            value=(
                "yes"
                if decision.action.value == "hand_off_to_human"
                else "no"
            ),
        ),
        WebDemoEvent(type="response", value="generated and stored"),
    ]
    return WebDemoChatResponse(
        session_id=payload.session_id,
        reply=reply,
        decision=decision,
        events=events,
    )
