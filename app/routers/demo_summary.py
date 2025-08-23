from fastapi import APIRouter

from dtos.demo import Demo

router = APIRouter(
    prefix="/demo",
    tags=["demo"],
)


@router.get("/", summary="汎用デモエンドポイント")
async def demo() -> Demo:
    return Demo(message="Hello, FastAPI!")
