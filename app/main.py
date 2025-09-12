from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routers.demo_mail import router as demo_mail_router
from routers.demo_rules import router as demo_rules_router
from routers.demo_summary import router as demo_summary_router
from sqlmodel import SQLModel
from starlette.middleware.cors import CORSMiddleware

from services.database.engine import get_engine
from services.database.seed import seed_core_data
from utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator:
    engine = get_engine()
    try:
        SQLModel.metadata.create_all(engine)
        seed_core_data(engine)
        yield
    except Exception:
        logger.exception("Error during lifespan")
    finally:
        engine.dispose()


def setup_server() -> FastAPI:
    """Setup the FastAPI server with CORS middleware."""
    # NOTE: lifespan 引数のtypo修正 (license -> lifespan)
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    routers = [
        ("api", demo_summary_router),
        ("api", demo_mail_router),
        ("api", demo_rules_router),
    ]

    for prefix, router in routers:
        app.include_router(router, prefix=f"/{prefix}")

    return app


app = setup_server()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
