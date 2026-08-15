import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.models import FaqEntry
from app.schemas.rag import RagAnswer
from app.services.faq import FaqService


def test_returns_best_verified_faq_answer() -> None:
    repository = MagicMock()
    repository.list_active = AsyncMock(
        return_value=[
            FaqEntry(
                question="Where is the clinic located?",
                answer="Verified location answer",
                keywords="address location directions",
            ),
            FaqEntry(
                question="What are the opening hours?",
                answer="Verified hours answer",
                keywords="hours opening schedule",
            ),
        ]
    )
    service = FaqService(repository)

    answer = asyncio.run(service.find_answer("What are your opening hours?"))

    assert answer == "Verified hours answer"


def test_returns_none_without_verified_match() -> None:
    repository = MagicMock()
    repository.list_active = AsyncMock(
        return_value=[
            FaqEntry(
                question="Where is the clinic located?",
                answer="Verified location answer",
                keywords="address location directions",
            )
        ]
    )

    answer = asyncio.run(
        FaqService(repository).find_answer("Do you have parking?")
    )

    assert answer is None


def test_prefers_grounded_rag_answer_over_database_faq() -> None:
    repository = MagicMock()
    repository.list_active = AsyncMock()
    knowledge_answerer = MagicMock()
    knowledge_answerer.answer = AsyncMock(
        return_value=RagAnswer(
            text="Grounded PDF answer",
            source_labels=["NSDC-KB-001, page 5, IMG-US-01"],
        )
    )

    answer = asyncio.run(
        FaqService(
            repository,
            knowledge_answerer=knowledge_answerer,
        ).find_answer("How do I prepare for an ultrasound?")
    )

    assert answer == "Grounded PDF answer"
    repository.list_active.assert_not_awaited()
