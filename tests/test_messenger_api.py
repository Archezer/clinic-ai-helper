import hashlib
import hmac
import json
from typing import Any

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings, get_settings
from app.dependencies import get_chat_service
from app.main import app
from app.services.exceptions import DuplicateMessageError


VERIFY_TOKEN = "test-verify-token"
APP_SECRET = "test-app-secret"


class RecordingChatService:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def process_message(self, **kwargs: str) -> None:
        self.calls.append(kwargs)


class DuplicateChatService:
    async def process_message(self, **kwargs: str) -> None:
        raise DuplicateMessageError("Duplicate test message")


def build_test_settings() -> Settings:
    return Settings(
        openrouter_api_key=SecretStr("test-openrouter-key"),
        openrouter_model="test-model",
        database_url=SecretStr("postgresql+asyncpg://test:test@db/test"),
        meta_verify_token=SecretStr(VERIFY_TOKEN),
        meta_app_secret=SecretStr(APP_SECRET),
    )


def signed_body(payload: dict[str, Any]) -> tuple[bytes, str]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    digest = hmac.new(
        APP_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return body, f"sha256={digest}"


def messenger_payload() -> dict[str, Any]:
    return {
        "object": "page",
        "entry": [
            {
                "messaging": [
                    {
                        "sender": {"id": "facebook-user-123"},
                        "message": {
                            "mid": "mid.message-123",
                            "text": "Hello",
                        },
                    }
                ]
            }
        ],
    }


def test_verifies_webhook() -> None:
    app.dependency_overrides[get_settings] = build_test_settings
    try:
        with TestClient(app) as client:
            response = client.get(
                "/webhooks/messenger",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": VERIFY_TOKEN,
                    "hub.challenge": "challenge-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.text == "challenge-123"


def test_rejects_invalid_verification_token() -> None:
    app.dependency_overrides[get_settings] = build_test_settings
    try:
        with TestClient(app) as client:
            response = client.get(
                "/webhooks/messenger",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "wrong-token",
                    "hub.challenge": "challenge-123",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_processes_signed_text_message() -> None:
    service = RecordingChatService()
    body, signature = signed_body(messenger_payload())
    app.dependency_overrides[get_settings] = build_test_settings
    app.dependency_overrides[get_chat_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhooks/messenger",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": signature,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert service.calls == [
        {
            "message": "Hello",
            "channel": "messenger",
            "external_user_id": "facebook-user-123",
            "external_message_id": "mid.message-123",
        }
    ]


def test_rejects_invalid_signature() -> None:
    service = RecordingChatService()
    body, _ = signed_body(messenger_payload())
    app.dependency_overrides[get_settings] = build_test_settings
    app.dependency_overrides[get_chat_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhooks/messenger",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": "sha256=invalid",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert service.calls == []


def test_acknowledges_duplicate_message() -> None:
    body, signature = signed_body(messenger_payload())
    app.dependency_overrides[get_settings] = build_test_settings
    app.dependency_overrides[get_chat_service] = DuplicateChatService
    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhooks/messenger",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": signature,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
