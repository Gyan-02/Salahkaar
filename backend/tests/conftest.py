import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models as registered_models
from app.api.pipeline import AnalysisPipeline
from app.config.database import Base, get_db
from app.engines.profile_builder import ProfileBuilder
from app.engines.program_registry import ProgramRegistry
from app.main import app


@pytest.fixture(scope="session")
def mock_cases() -> list[dict[str, Any]]:
    path = Path(__file__).parents[1] / "app" / "data" / "mock_cases.json"
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


@pytest.fixture
def registry() -> ProgramRegistry:
    return ProgramRegistry()


@pytest.fixture
def profile_builder() -> ProfileBuilder:
    return ProfileBuilder()


@pytest.fixture
def pipeline() -> AnalysisPipeline:
    return AnalysisPipeline()


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    original_overrides = dict(app.dependency_overrides)
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        session = testing_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, testing_session
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)
    Base.metadata.drop_all(engine)
    engine.dispose()
