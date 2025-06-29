from dtos.demo import Demo
from fastapi import APIRouter

router = APIRouter(
    prefix="/demo",
    tags=["demo"],
)


@router.get("/")
async def demo() -> Demo:
    return Demo(message="Hello, FastAPI!")
