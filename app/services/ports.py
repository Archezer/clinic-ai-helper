from typing import Protocol

from app.schemas.rag import RagAnswer


class MessageSender(Protocol):
    async def send_text(
        self,
        recipient_id: str,
        text: str,
    ) -> None: ...


class KnowledgeAnswerer(Protocol):
    async def answer(self, question: str) -> RagAnswer | None: ...
