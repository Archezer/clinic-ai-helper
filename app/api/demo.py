from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter(tags=["demo"])


@router.get("/demo", include_in_schema=False)
async def demo_page() -> FileResponse:
    return FileResponse(
        Path(__file__).resolve().parent.parent / "static" / "demo.html"
    )
