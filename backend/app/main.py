from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_analysis_pipeline
from app.api.routes import ROUTERS
from app.config.settings import get_settings
from app.engines.program_registry import ProgramNotFoundError
from app.rag.dependencies import get_grounded_analysis_pipeline
from app.rag.router import router as guideline_router
from app.services.extraction.base import ExtractionError


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    upload_path = get_settings().upload_path
    upload_path.mkdir(parents=True, exist_ok=True)
    _remove_abandoned_uploads(upload_path)
    yield
    _remove_abandoned_uploads(upload_path)


def _remove_abandoned_uploads(upload_path: Path) -> None:
    for path in upload_path.iterdir():
        if path.is_file() and path.name != ".gitkeep":
            path.unlink(missing_ok=True)


async def program_not_found(_: Request, exc: ProgramNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def extraction_failed(_: Request, exc: ExtractionError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": str(exc)},
    )


def create_app(extra_routers: Iterable[APIRouter] = ()) -> FastAPI:
    application = FastAPI(
        title="Benefits Readiness Navigator",
        version="0.1.0",
        description="Eligibility and application-readiness analysis for a local MVP demo.",
        lifespan=lifespan,
    )
    for router in [*ROUTERS, guideline_router, *extra_routers]:
        application.include_router(router)
    application.add_exception_handler(ProgramNotFoundError, program_not_found)
    application.add_exception_handler(ExtractionError, extraction_failed)
    application.dependency_overrides[get_analysis_pipeline] = (
        get_grounded_analysis_pipeline
    )
    return application


app = create_app()
