import os
from urllib.parse import urlparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.config.settings import get_settings


@pytest.mark.postgres_integration
def test_migration_round_trip_on_real_postgres(monkeypatch) -> None:
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL is not configured")
    database_name = urlparse(url.replace("postgresql+psycopg", "postgresql", 1)).path.lstrip("/")
    if "test" not in database_name.casefold():
        pytest.fail("Refusing migration round-trip: database name must contain 'test'")

    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    config = Config("alembic.ini")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    command.upgrade(config, "head")

    engine = create_engine(url)
    try:
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "documents",
            "citizen_profiles",
            "analyses",
        }
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260621_0001"
            assert connection.dialect.name == "postgresql"
        analysis_columns = {column["name"]: column for column in inspector.get_columns("analyses")}
        assert analysis_columns["eligible"]["nullable"] is True
        assert analysis_columns["readiness_score"]["nullable"] is True
    finally:
        engine.dispose()
        get_settings.cache_clear()
