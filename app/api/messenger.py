import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.dependencies import get_chat_service
from app.integrations.messenger import is_valid_signature
from app.schemas.messenger import MessengerWebhookPayload
from app.services.chat import ChatService
from app.services.exceptions import DuplicateMessageError


router = APIRouter(prefix="/webhooks/messenger", tags=["messenger"])

SettingsDependency = Annotated[Settings, Depends(get_settings)]
ChatServiceDependency = Annotated[ChatService, Depends(get_chat_service)]


@router.get("")
async def verify_webhook(
    settings: SettingsDependency,
    mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    verify_token: Annotated[
        str | None,
        Query(alias="hub.verify_token"),
    ] = None,
    challenge: Annotated[
        str | None,
        Query(alias="hub.challenge"),
    ] = None,
) -> PlainTextResponse:
    configured_token = settings.meta_verify_token
    if configured_token is None or not configured_token.get_secret_value():
        raise HTTPException(
            status_code=503,
            detail="Messenger webhook is not configured.",
        )

    token_matches = hmac.compare_digest(
        verify_token or "",
        configured_token.get_secret_value(),
    )
    if mode != "subscribe" or not token_matches or challenge is None:
        raise HTTPException(status_code=403, detail="Verification failed.")

    return PlainTextResponse(challenge)


@router.post("")
async def receive_webhook(
    request: Request,
    settings: SettingsDependency,
    chat_service: ChatServiceDependency,
    signature: Annotated[
        str | None,
        Header(alias="X-Hub-Signature-256"),
    ] = None,
) -> JSONResponse:
    app_secret = settings.meta_app_secret
    if app_secret is None or not app_secret.get_secret_value():
        raise HTTPException(
            status_code=503,
            detail="Messenger webhook is not configured.",
        )

    body = await request.body()
    if not is_valid_signature(
        body=body,
        signature=signature,
        app_secret=app_secret.get_secret_value(),
    ):
        raise HTTPException(status_code=403, detail="Invalid signature.")

    try:
        payload = MessengerWebhookPayload.model_validate_json(body)
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="Invalid Messenger payload.",
        ) from error

    for entry in payload.entry:
        for event in entry.messaging:
            message = event.message
            if message is None or message.text is None or message.is_echo:
                continue

            try:
                await chat_service.process_message(
                    message=message.text,
                    channel="messenger",
                    external_user_id=event.sender.id,
                    external_message_id=message.mid,
                )
            except DuplicateMessageError:
                continue

    return JSONResponse({"status": "ok"})
