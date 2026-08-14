from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.database import Database
from app.services.chat import ChatService
from app.services.classifier import MessageClassifier
from app.services.exceptions import ClassificationUnavailableError
from app.services.router import MessageRouter


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

    message_router = MessageRouter()

    application.state.message_classifier = message_classifier
    application.state.database = database
    application.state.chat_service = ChatService(
        classifier=message_classifier,
        router=message_router
    )

    yield

    await database.dispose()
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


app.include_router(health_router)
app.include_router(chat_router)
