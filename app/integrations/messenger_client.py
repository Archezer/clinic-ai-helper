import httpx

from app.services.exceptions import MessageDeliveryError


class MessengerClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        page_access_token: str,
        graph_base_url: str,
        graph_api_version: str,
    ) -> None:
        self._http_client = http_client
        self._page_access_token = page_access_token
        self._messages_url = (
            f"{graph_base_url.rstrip('/')}/"
            f"{graph_api_version.strip('/')}/me/messages"
        )

    async def send_text(
        self,
        recipient_id: str,
        text: str,
    ) -> None:
        if not self._page_access_token:
            raise MessageDeliveryError(
                "Messenger page access token is not configured"
            )

        try:
            response = await self._http_client.post(
                self._messages_url,
                params={"access_token": self._page_access_token},
                json={
                    "recipient": {"id": recipient_id},
                    "messaging_type": "RESPONSE",
                    "message": {"text": text},
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise MessageDeliveryError(
                "Messenger Send API request failed"
            ) from error
