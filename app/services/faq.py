import re

from app.models import FaqEntry
from app.repositories import FaqRepository
from app.services.ports import KnowledgeAnswerer


TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)


def tokenize(value: str) -> set[str]:
    return {
        token.casefold()
        for token in TOKEN_PATTERN.findall(value)
        if len(token) >= 3
    }


class FaqService:
    def __init__(
        self,
        repository: FaqRepository,
        knowledge_answerer: KnowledgeAnswerer | None = None,
    ) -> None:
        self._repository = repository
        self._knowledge_answerer = knowledge_answerer

    async def find_answer(self, message: str) -> str | None:
        if self._knowledge_answerer is not None:
            rag_answer = await self._knowledge_answerer.answer(message)
            if rag_answer is not None:
                return rag_answer.text

        query_tokens = tokenize(message)
        if not query_tokens:
            return None

        entries = await self._repository.list_active()
        best_entry: FaqEntry | None = None
        best_score = 0
        for entry in entries:
            entry_tokens = tokenize(f"{entry.question} {entry.keywords}")
            score = len(query_tokens & entry_tokens)
            if score > best_score:
                best_entry = entry
                best_score = score

        return best_entry.answer if best_entry is not None else None
