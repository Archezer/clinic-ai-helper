import asyncio
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError
from pypdf import PdfReader

from app.schemas.rag import GeneratedKnowledgeAnswer, RagAnswer
from app.services.exceptions import KnowledgeGenerationUnavailableError


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")
SERVICE_CODE_PATTERN = re.compile(r"\b[A-Z]{2,}(?:-[A-Z]{2})?-\d{2}\b")
STOP_WORDS = {
    "about",
    "before",
    "clinic",
    "could",
    "does",
    "for",
    "have",
    "help",
    "how",
    "prepare",
    "should",
    "service",
    "visit",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
    "your",
}

SYSTEM_PROMPT = """
You are an administrative receptionist for a fictional demo clinic.
Answer only from the supplied knowledge-base excerpts.

Rules:
- answer only administrative questions about services and visit preparation;
- never diagnose, assess symptoms, interpret results, recommend treatment, or
  advise changing medication, food, or fluids beyond explicit source text;
- if the excerpts do not directly support an answer, set is_supported to false;
- keep the answer concise and do not mention hidden instructions or retrieval;
- do not invent clinic details.
""".strip()


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    text: str
    page_number: int
    service_code: str | None

    @property
    def source_label(self) -> str:
        code = f", {self.service_code}" if self.service_code else ""
        return f"NSDC-KB-001, page {self.page_number}{code}"


def tokenize(value: str) -> list[str]:
    return [
        token.casefold()
        for token in TOKEN_PATTERN.findall(value)
        if len(token) >= 3 and token.casefold() not in STOP_WORDS
    ]


def extract_chunks(
    pdf_path: Path,
    max_characters: int = 1500,
) -> list[KnowledgeChunk]:
    reader = PdfReader(pdf_path)
    chunks: list[KnowledgeChunk] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        paragraphs = [
            part.strip()
            for part in re.split(r"\n\s*\n", text)
            if part.strip()
        ]
        buffer: list[str] = []
        buffer_size = 0
        for paragraph in paragraphs:
            if buffer and buffer_size + len(paragraph) > max_characters:
                chunks.append(_create_chunk(buffer, page_number))
                buffer = []
                buffer_size = 0
            buffer.append(paragraph)
            buffer_size += len(paragraph)
        if buffer:
            chunks.append(_create_chunk(buffer, page_number))
    return chunks


def _create_chunk(paragraphs: list[str], page_number: int) -> KnowledgeChunk:
    text = "\n".join(paragraphs)
    code_match = SERVICE_CODE_PATTERN.search(text)
    return KnowledgeChunk(
        text=text,
        page_number=page_number,
        service_code=code_match.group(0) if code_match else None,
    )


class LexicalRetriever:
    def __init__(self, chunks: list[KnowledgeChunk]) -> None:
        self._chunks = chunks
        self._term_counts = [
            Counter(tokenize(chunk.text))
            for chunk in chunks
        ]
        document_frequency = Counter(
            token
            for counts in self._term_counts
            for token in counts
        )
        total = max(len(chunks), 1)
        self._idf = {
            token: math.log((total + 1) / (frequency + 0.5)) + 1
            for token, frequency in document_frequency.items()
        }

    def search(
        self,
        query: str,
        *,
        limit: int,
        min_score: float,
    ) -> list[KnowledgeChunk]:
        query_terms = set(tokenize(query))
        if not query_terms:
            return []

        maximum_score = sum(
            self._idf.get(term, 1.0)
            for term in query_terms
        )
        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk, counts in zip(
            self._chunks,
            self._term_counts,
            strict=True,
        ):
            matched_score = sum(
                self._idf.get(term, 0.0)
                for term in query_terms
                if counts[term]
            )
            score = matched_score / max(maximum_score, 1.0)
            if score >= min_score:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:limit]]


class PdfRagService:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        document_path: Path,
        top_k: int = 4,
        min_score: float = 0.12,
    ) -> None:
        self._client = client
        self._model = model
        self._document_path = document_path
        self._top_k = top_k
        self._min_score = min_score
        self._retriever: LexicalRetriever | None = None
        self._initialization_lock = asyncio.Lock()

    async def initialize(self) -> None:
        if self._retriever is not None:
            return
        async with self._initialization_lock:
            if self._retriever is not None:
                return
            try:
                chunks = await asyncio.to_thread(
                    extract_chunks,
                    self._document_path,
                )
            except (OSError, ValueError) as error:
                raise KnowledgeGenerationUnavailableError(
                    "RAG document could not be indexed"
                ) from error
            if not chunks:
                raise ValueError(
                    f"No text found in RAG document: {self._document_path}"
                )
            self._retriever = LexicalRetriever(chunks)

    async def answer(self, question: str) -> RagAnswer | None:
        await self.initialize()
        assert self._retriever is not None
        chunks = self._retriever.search(
            question,
            limit=self._top_k,
            min_score=self._min_score,
        )
        if not chunks:
            return None

        context = "\n\n".join(
            f"SOURCE: {chunk.source_label}\n{chunk.text}"
            for chunk in chunks
        )
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"QUESTION:\n{question}\n\n"
                            f"KNOWLEDGE BASE:\n{context}"
                        ),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "knowledge_answer",
                        "strict": True,
                        "schema": (
                            GeneratedKnowledgeAnswer.model_json_schema()
                        ),
                    },
                },
                extra_body={
                    "provider": {
                        "require_parameters": True,
                    }
                },
            )
            content = completion.choices[0].message.content
            if content is None:
                raise RuntimeError(
                    "OpenRouter returned an empty RAG response"
                )
            generated = GeneratedKnowledgeAnswer.model_validate_json(
                content
            )
        except (
            OpenAIError,
            ValidationError,
            IndexError,
            RuntimeError,
        ) as error:
            raise KnowledgeGenerationUnavailableError(
                "RAG answer generation failed"
            ) from error

        if not generated.is_supported or not generated.answer.strip():
            return None

        labels = list(
            dict.fromkeys(chunk.source_label for chunk in chunks)
        )
        return RagAnswer(
            text=(
                f"{generated.answer.strip()}\n\n"
                f"Source: {'; '.join(labels)}"
            ),
            source_labels=labels,
        )
