from fastapi import APIRouter

from dtos.demo import Demo

router = APIRouter(
    prefix="/demo",
    tags=["demo"],
)


@router.get("/")
async def demo() -> Demo:
    return Demo(message="Hello, FastAPI!")
