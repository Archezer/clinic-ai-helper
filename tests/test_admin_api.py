from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.dependencies import get_handoff_service
from app.main import app
from app.models import Conversation, ConversationStatus


class StubHandoffService:
    async def list_pending(self) -> list[Conversation]:
        now = datetime.now(UTC)
        return [
            Conversation(
                id=uuid4(),
                channel="messenger",
                external_user_id="facebook-user-123",
                status=ConversationStatus.NEEDS_HUMAN,
                created_at=now,
                updated_at=now,
            )
        ]


def test_requires_admin_token() -> None:
    app.dependency_overrides[get_handoff_service] = StubHandoffService
    try:
        with TestClient(app) as client:
            client.app.state.settings.admin_api_token = SecretStr(
                "test-admin-token"
            )
            response = client.get("/admin/handoffs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_lists_handoffs_with_valid_admin_token() -> None:
    app.dependency_overrides[get_handoff_service] = StubHandoffService
    try:
        with TestClient(app) as client:
            client.app.state.settings.admin_api_token = SecretStr(
                "test-admin-token"
            )
            response = client.get(
                "/admin/handoffs",
                headers={"X-Admin-Token": "test-admin-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["status"] == "needs_human"
