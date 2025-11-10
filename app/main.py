from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI
from sqlmodel import SQLModel
from starlette.middleware.cors import CORSMiddleware

from app_resources import app_resources
from routers import messages_router, rules_router, search_router, summary_router
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


def startup() -> None:
    app_resources.load_model()


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

    @app.post("/trigger-startup")
    async def trigger_startup(background_tasks: BackgroundTasks) -> dict[str, str]:
        background_tasks.add_task(startup)
        return {"status": "startup triggered"}

    routers = [
        ("api", messages_router),
        ("api", rules_router),
        ("api", search_router),
        ("api", summary_router),
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
