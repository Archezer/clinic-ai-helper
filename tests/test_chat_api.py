from fastapi.testclient import TestClient

from app.dependencies import get_chat_service, get_message_classifier
from app.main import app
from app.schemas.classification import Intent, MessageClassification
from app.schemas.routing import ChatAction, RoutingDecision
from app.services.exceptions import (
    ClassificationUnavailableError,
    DuplicateMessageError,
    MessageDeliveryError,
)


class SuccessfulClassifier:
    async def classify(self, message: str) -> MessageClassification:
        return MessageClassification(intent=Intent.BOOK_APPOINTMENT)


class FailingClassifier:
    async def classify(self, message: str) -> MessageClassification:
        raise ClassificationUnavailableError("Test classification failure")


class SuccessfulChatService:
    async def process_message(
        self,
        message: str,
        channel: str,
        external_user_id: str,
        external_message_id: str,
    ) -> RoutingDecision:
        return RoutingDecision(
            intent=Intent.MEDICAL_QUESTION,
            action=ChatAction.HAND_OFF_TO_HUMAN,
        )


class DuplicateChatService:
    async def process_message(
        self,
        message: str,
        channel: str,
        external_user_id: str,
        external_message_id: str,
    ) -> RoutingDecision:
        raise DuplicateMessageError("Duplicate test message")


class FailingDeliveryChatService:
    async def process_message(
        self,
        message: str,
        channel: str,
        external_user_id: str,
        external_message_id: str,
    ) -> RoutingDecision:
        raise MessageDeliveryError("Meta request failed")


def test_classify_message() -> None:
    app.dependency_overrides[get_message_classifier] = (
        lambda: SuccessfulClassifier()
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat/classify",
                json={"message": "I want to book an appointment"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"intent": "book_appointment"}


def test_reject_empty_message() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/chat/classify",
            json={"message": ""},
        )

    assert response.status_code == 422


def test_returns_503_when_classification_fails() -> None:
    app.dependency_overrides[get_message_classifier] = (
        lambda: FailingClassifier()
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat/classify",
                json={"message": "Some message"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Message classification is temporarily unavailable."
    }


def test_processes_message() -> None:
    app.dependency_overrides[get_chat_service] = (
        lambda: SuccessfulChatService()
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat/process",
                json={
                    "message": "Can you recommend a medication?",
                    "channel": "messenger",
                    "external_user_id": "facebook-user-123",
                    "external_message_id": "mid.medical-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "intent": "medical_question",
        "action": "hand_off_to_human",
    }


def test_returns_409_for_duplicate_message() -> None:
    app.dependency_overrides[get_chat_service] = (
        lambda: DuplicateChatService()
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat/process",
                json={
                    "message": "Hello again",
                    "channel": "messenger",
                    "external_user_id": "facebook-user-123",
                    "external_message_id": "mid.duplicate-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Message has already been processed."
    }


def test_returns_502_when_message_delivery_fails() -> None:
    app.dependency_overrides[get_chat_service] = (
        lambda: FailingDeliveryChatService()
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat/process",
                json={
                    "message": "Hello",
                    "channel": "messenger",
                    "external_user_id": "facebook-user-123",
                    "external_message_id": "mid.failed-delivery-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Message delivery is temporarily unavailable."
    }
