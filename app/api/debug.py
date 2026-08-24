from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import (
    FakeMessengerSession,
    get_fake_messenger_session,
)
from app.schemas.debug import (
    FakeMessengerRequest,
    FakeMessengerResponse,
    FakeOutgoingMessage,
)


router = APIRouter(prefix="/debug", tags=["debug"])

FakeSessionDependency = Annotated[
    FakeMessengerSession,
    Depends(get_fake_messenger_session),
]


@router.post(
    "/messenger/messages",
    response_model=FakeMessengerResponse,
)
async def simulate_messenger_message(
    payload: FakeMessengerRequest,
    fake_session: FakeSessionDependency,
) -> FakeMessengerResponse:
    decision = await fake_session.chat_service.process_message(
        message=payload.text,
        channel="messenger",
        external_user_id=payload.sender_id,
        external_message_id=payload.message_id,
    )
    return FakeMessengerResponse(
        decision=decision,
        outgoing_messages=[
            FakeOutgoingMessage(
                recipient_id=message.recipient_id,
                text=message.text,
            )
            for message in fake_session.message_sender.messages
        ],
    )
