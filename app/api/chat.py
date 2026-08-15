from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_chat_service, get_message_classifier
from app.schemas.chat import ChatRequest, ProcessMessageRequest
from app.schemas.classification import MessageClassification
from app.schemas.routing import RoutingDecision
from app.services.chat import ChatService
from app.services.classifier import MessageClassifier

router = APIRouter(prefix="/chat", tags=["chat"])


ClassifierDependency = Annotated[
    MessageClassifier,
    Depends(get_message_classifier),
]

ChatServiceDependency = Annotated[
    ChatService,
    Depends(get_chat_service),
]


@router.post("/classify", response_model=MessageClassification)
async def classify_message(
    request: ChatRequest,
    classifier: ClassifierDependency,
) -> MessageClassification:
    return await classifier.classify(request.message)


@router.post("/process", response_model=RoutingDecision)
async def process_message(
    request: ProcessMessageRequest,
    chat_service: ChatServiceDependency,
) -> RoutingDecision:
    return await chat_service.process_message(
        message=request.message,
        channel=request.channel,
        external_user_id=request.external_user_id,
        external_message_id=request.external_message_id,
    )
