import hmac
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.dependencies import get_admin_operations_service, get_handoff_service
from app.schemas.admin import (
    AdminActionResponse,
    AppointmentQueueItem,
    AppointmentStatusRequest,
    ConversationSummary,
    FaqCreateRequest,
    FaqView,
    HumanReplyRequest,
    MessageView,
)
from app.services.admin_operations import (
    AdminOperationsService,
    AppointmentNotFoundError,
)
from app.services.handoff import (
    ConversationNotFoundError,
    ConversationStateError,
    HandoffService,
)


router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_token(
    request: Request,
    token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> None:
    configured_token = request.app.state.settings.admin_api_token
    if configured_token is None or not configured_token.get_secret_value():
        raise HTTPException(status_code=503, detail="Admin API is not configured.")
    if not hmac.compare_digest(token or "", configured_token.get_secret_value()):
        raise HTTPException(status_code=401, detail="Invalid admin token.")


AdminAuth = Annotated[None, Depends(require_admin_token)]
HandoffDependency = Annotated[HandoffService, Depends(get_handoff_service)]
OperationsDependency = Annotated[
    AdminOperationsService,
    Depends(get_admin_operations_service),
]


@router.get(
    "/handoffs",
    response_model=list[ConversationSummary],
)
async def list_handoffs(
    auth: AdminAuth,
    service: HandoffDependency,
) -> list[ConversationSummary]:
    conversations = await service.list_pending()
    return [ConversationSummary.model_validate(item) for item in conversations]


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageView],
)
async def get_conversation_history(
    conversation_id: UUID,
    auth: AdminAuth,
    service: HandoffDependency,
) -> list[MessageView]:
    try:
        messages = await service.get_history(conversation_id)
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    return [MessageView.model_validate(item) for item in messages]


@router.post(
    "/conversations/{conversation_id}/reply",
    response_model=AdminActionResponse,
)
async def reply_to_conversation(
    conversation_id: UUID,
    body: HumanReplyRequest,
    auth: AdminAuth,
    service: HandoffDependency,
) -> AdminActionResponse:
    try:
        await service.reply(conversation_id, body.message)
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    except ConversationStateError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return AdminActionResponse(status="sent")


@router.post(
    "/conversations/{conversation_id}/close",
    response_model=AdminActionResponse,
)
async def close_conversation(
    conversation_id: UUID,
    auth: AdminAuth,
    service: HandoffDependency,
) -> AdminActionResponse:
    try:
        await service.close(conversation_id)
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail="Conversation not found.") from error
    return AdminActionResponse(status="closed")


@router.get("/faqs", response_model=list[FaqView])
async def list_faqs(
    auth: AdminAuth,
    service: OperationsDependency,
) -> list[FaqView]:
    entries = await service.list_faqs()
    return [FaqView.model_validate(entry) for entry in entries]


@router.post("/faqs", response_model=FaqView, status_code=201)
async def create_faq(
    body: FaqCreateRequest,
    auth: AdminAuth,
    service: OperationsDependency,
) -> FaqView:
    entry = await service.create_faq(
        question=body.question,
        answer=body.answer,
        keywords=body.keywords,
    )
    return FaqView.model_validate(entry)


@router.get(
    "/appointments",
    response_model=list[AppointmentQueueItem],
)
async def list_appointment_requests(
    auth: AdminAuth,
    service: OperationsDependency,
) -> list[AppointmentQueueItem]:
    records = await service.list_appointment_requests()
    return [AppointmentQueueItem.model_validate(record) for record in records]


@router.patch(
    "/appointments/{appointment_id}",
    response_model=AdminActionResponse,
)
async def update_appointment_status(
    appointment_id: UUID,
    body: AppointmentStatusRequest,
    auth: AdminAuth,
    service: OperationsDependency,
) -> AdminActionResponse:
    try:
        await service.set_appointment_status(appointment_id, body.status)
    except AppointmentNotFoundError as error:
        raise HTTPException(status_code=404, detail="Appointment not found.") from error
    return AdminActionResponse(status=body.status.value)
