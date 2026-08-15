from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.messenger import router as messenger_router
from app.core.config import get_settings
from app.core.database import Database
from app.services.classifier import MessageClassifier
from app.services.exceptions import (
    ClassificationUnavailableError,
    DuplicateMessageError,
    KnowledgeGenerationUnavailableError,
    MessageDeliveryError,
)
from app.services.rag import PdfRagService


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    database = Database(
    url=settings.database_url.get_secret_value()
    )

    openrouter_client = AsyncOpenAI(
        api_key=settings.openrouter_api_key.get_secret_value(),
        base_url=settings.openrouter_base_url,
    )

    message_classifier = MessageClassifier(
        client = openrouter_client,
        model = settings.openrouter_model
    )
    rag_service = PdfRagService(
        client=openrouter_client,
        model=settings.openrouter_model,
        document_path=Path(settings.rag_document_path),
        top_k=settings.rag_top_k,
        min_score=settings.rag_min_score,
    )
    http_client = httpx.AsyncClient(timeout=10.0)

    application.state.settings = settings
    application.state.message_classifier = message_classifier
    application.state.rag_service = rag_service
    application.state.database = database
    application.state.http_client = http_client
    
    yield

    await database.dispose()
    await http_client.aclose()
    await openrouter_client.close()


app = FastAPI(
    title="Clinic AI Receptionist",
    lifespan=lifespan,
)


@app.exception_handler(ClassificationUnavailableError)
async def handle_classification_error(
    request: Request,
    error: ClassificationUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Message classification is temporarily unavailable."
        },
    )


@app.exception_handler(DuplicateMessageError)
async def handle_duplicate_message(
    request: Request,
    error: DuplicateMessageError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "Message has already been processed."},
    )


@app.exception_handler(MessageDeliveryError)
async def handle_message_delivery_error(
    request: Request,
    error: MessageDeliveryError,
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": "Message delivery is temporarily unavailable."},
    )


@app.exception_handler(KnowledgeGenerationUnavailableError)
async def handle_knowledge_generation_error(
    request: Request,
    error: KnowledgeGenerationUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Knowledge answer generation is temporarily unavailable."
            )
        },
    )


app.include_router(health_router)
app.include_router(chat_router)
app.include_router(messenger_router)
app.include_router(admin_router)
