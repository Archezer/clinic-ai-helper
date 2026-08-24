from fastapi.testclient import TestClient

from app.dependencies import FakeMessengerSession, get_fake_messenger_session
from app.integrations.fake_messenger import FakeMessageSender
from app.main import app
from app.schemas.classification import Intent
from app.schemas.routing import ChatAction, RoutingDecision


class FakeChatService:
    def __init__(self, sender: FakeMessageSender) -> None:
        self._sender = sender

    async def process_message(
        self,
        message: str,
        channel: str,
        external_user_id: str,
        external_message_id: str,
    ) -> RoutingDecision:
        await self._sender.send_text(
            recipient_id=external_user_id,
            text=f"Fake reply to: {message}",
        )
        return RoutingDecision(
            intent=Intent.CLINIC_FAQ,
            action=ChatAction.ANSWER_FAQ,
        )


def test_returns_captured_fake_messenger_reply() -> None:
    sender = FakeMessageSender()
    fake_session = FakeMessengerSession(
        chat_service=FakeChatService(sender),  # type: ignore[arg-type]
        message_sender=sender,
    )
    app.dependency_overrides[get_fake_messenger_session] = (
        lambda: fake_session
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/debug/messenger/messages",
                json={
                    "sender_id": "demo-user",
                    "message_id": "demo-message-1",
                    "text": "How do I prepare for an ultrasound?",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "decision": {
            "intent": "clinic_faq",
            "action": "answer_faq",
        },
        "outgoing_messages": [
            {
                "recipient_id": "demo-user",
                "text": (
                    "Fake reply to: How do I prepare for an ultrasound?"
                ),
            }
        ],
    }
