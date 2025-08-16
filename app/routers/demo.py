from fastapi import APIRouter

from dtos.demo import Demo
from dtos.demo_mail import DemoMailDTO, DemoSummaryDTO, demo_mail_value, demo_summary_value

router = APIRouter(
    prefix="/demo",
    tags=["demo"],
)


@router.get("/")
async def demo() -> Demo:
    return Demo(message="Hello, FastAPI!")


# ▼ 追加: メールのデモ値
@router.get("/mail", summary="メールのデモ値を返す")
async def get_demo_mail() -> DemoMailDTO:
    return demo_mail_value()


# ▼ 追加: サマリのデモ値
@router.get("/summary", summary="サマリのデモ値を返す")
async def get_demo_summary() -> DemoSummaryDTO:
    return demo_summary_value()
