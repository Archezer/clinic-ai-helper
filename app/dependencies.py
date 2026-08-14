from fastapi import Request

from app.services.chat import ChatService
from app.services.classifier import MessageClassifier


def get_message_classifier(request: Request) -> MessageClassifier:
    return request.app.state.message_classifier

def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service