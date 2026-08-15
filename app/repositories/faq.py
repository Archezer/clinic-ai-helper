from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FaqEntry


class FaqRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[FaqEntry]:
        statement = (
            select(FaqEntry)
            .where(FaqEntry.is_active.is_(True))
            .order_by(FaqEntry.created_at)
        )
        result = await self._session.scalars(statement)
        return list(result.all())

    async def create(
        self,
        question: str,
        answer: str,
        keywords: str,
    ) -> FaqEntry:
        entry = FaqEntry(
            question=question,
            answer=answer,
            keywords=keywords,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
