import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.services.rag import KnowledgeChunk, LexicalRetriever, PdfRagService


def test_retriever_returns_matching_service_chunk() -> None:
    ultrasound = KnowledgeChunk(
        text=(
            "Diagnostic ultrasound visit. Follow written eating, drinking, "
            "or bladder preparation instructions for the exact exam."
        ),
        page_number=5,
        service_code="IMG-US-01",
    )
    laboratory = KnowledgeChunk(
        text=(
            "Routine laboratory collection. Do not assume fasting is "
            "required."
        ),
        page_number=4,
        service_code="LAB-01",
    )
    retriever = LexicalRetriever([ultrasound, laboratory])

    result = retriever.search(
        "How do I prepare for an ultrasound exam?",
        limit=1,
        min_score=0.1,
    )

    assert result == [ultrasound]


def test_retriever_returns_nothing_for_unrelated_question() -> None:
    retriever = LexicalRetriever(
        [
            KnowledgeChunk(
                text="Vaccination appointment and vaccination records.",
                page_number=8,
                service_code="VAX-01",
            )
        ]
    )

    result = retriever.search(
        "Is there parking near the building?",
        limit=4,
        min_score=0.12,
    )

    assert result == []


def test_rag_answer_contains_deterministic_source_label() -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock()
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = (
        '{"is_supported": true, "answer": '
        '"Bring the written laboratory order."}'
    )
    client.chat.completions.create.return_value = completion
    service = PdfRagService(
        client=client,
        model="test-model",
        document_path=MagicMock(),
    )
    service._retriever = LexicalRetriever(
        [
            KnowledgeChunk(
                text="Laboratory visit: bring the written laboratory order.",
                page_number=4,
                service_code="LAB-01",
            )
        ]
    )

    answer = asyncio.run(
        service.answer("What should I bring to the laboratory visit?")
    )

    assert answer is not None
    assert "Bring the written laboratory order." in answer.text
    assert answer.source_labels == ["NSDC-KB-001, page 4, LAB-01"]
    assert "NSDC-KB-001, page 4, LAB-01" in answer.text


def test_rag_rejects_unsupported_generated_answer() -> None:
    client = MagicMock()
    client.chat.completions.create = AsyncMock()
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = (
        '{"is_supported": false, "answer": ""}'
    )
    client.chat.completions.create.return_value = completion
    service = PdfRagService(
        client=client,
        model="test-model",
        document_path=MagicMock(),
    )
    service._retriever = LexicalRetriever(
        [
            KnowledgeChunk(
                text="Vaccination appointment records.",
                page_number=8,
                service_code="VAX-01",
            )
        ]
    )

    answer = asyncio.run(service.answer("Tell me about vaccination"))

    assert answer is None
