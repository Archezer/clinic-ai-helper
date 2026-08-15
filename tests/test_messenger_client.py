import asyncio
import json

import httpx
import pytest

from app.integrations.messenger_client import MessengerClient
from app.services.exceptions import MessageDeliveryError


def test_sends_text_message() -> None:
    captured_request: httpx.Request | None = None

    def handle_request(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json={"message_id": "mid.sent-123"})

    async def run_test() -> None:
        transport = httpx.MockTransport(handle_request)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = MessengerClient(
                http_client=http_client,
                page_access_token="test-page-token",
                graph_base_url="https://graph.facebook.test",
                graph_api_version="v-test",
            )
            await client.send_text(
                recipient_id="facebook-user-123",
                text="Hello from the clinic",
            )

    asyncio.run(run_test())

    assert captured_request is not None
    assert str(captured_request.url).startswith(
        "https://graph.facebook.test/v-test/me/messages"
    )
    assert captured_request.url.params["access_token"] == "test-page-token"
    assert json.loads(captured_request.content) == {
        "recipient": {"id": "facebook-user-123"},
        "messaging_type": "RESPONSE",
        "message": {"text": "Hello from the clinic"},
    }


def test_converts_provider_failure_to_application_error() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "failed"}})

    async def run_test() -> None:
        transport = httpx.MockTransport(handle_request)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = MessengerClient(
                http_client=http_client,
                page_access_token="test-page-token",
                graph_base_url="https://graph.facebook.test",
                graph_api_version="v-test",
            )
            await client.send_text("facebook-user-123", "Hello")

    with pytest.raises(MessageDeliveryError):
        asyncio.run(run_test())


def test_rejects_missing_page_access_token() -> None:
    async def run_test() -> None:
        async with httpx.AsyncClient() as http_client:
            client = MessengerClient(
                http_client=http_client,
                page_access_token="",
                graph_base_url="https://graph.facebook.test",
                graph_api_version="v-test",
            )
            await client.send_text("facebook-user-123", "Hello")

    with pytest.raises(MessageDeliveryError):
        asyncio.run(run_test())
