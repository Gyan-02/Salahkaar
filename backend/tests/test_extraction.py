import json
import logging
from types import SimpleNamespace

import pytest

from app.config.settings import Settings
from app.schemas.document import ExtractionInput
from app.services.extraction.base import ExtractionError
from app.services.extraction.gemini import GeminiExtractor
from app.services.extraction.mock import MockExtractor


@pytest.mark.asyncio
async def test_mock_extractor_uses_explicit_fields() -> None:
    result = await MockExtractor().extract(
        ExtractionInput(
            filename="land.json",
            content_type="application/json",
            content=b"",
            document_type="land_record",
            mock_fields={
                "owner_name": "Ravi Kumar",
                "land_ownership_date": "2018-10-01",
            },
        )
    )
    assert result.extractor == "mock"
    assert result.fields["land_ownership_date"] == "2018-10-01"


@pytest.mark.asyncio
async def test_mock_extractor_reads_json_fixture() -> None:
    content = json.dumps(
        {"document_type": "aadhaar", "fields": {"name": "Asha Devi"}}
    ).encode()
    result = await MockExtractor().extract(
        ExtractionInput(
            filename="aadhaar.json",
            content_type="application/json",
            content=content,
        )
    )
    assert result.document_type == "aadhaar"
    assert result.fields["name"] == "Asha Devi"


@pytest.mark.asyncio
async def test_mock_extractor_rejects_unknown_fields() -> None:
    with pytest.raises(ExtractionError, match="not in the aadhaar schema"):
        await MockExtractor().extract(
            ExtractionInput(
                filename="aadhaar.json",
                content_type="application/json",
                content=b"",
                document_type="aadhaar",
                mock_fields={"invented_field": "value"},
            )
        )


@pytest.mark.asyncio
async def test_mock_extractor_rejects_binary_without_mock_fields() -> None:
    with pytest.raises(ExtractionError, match="binary OCR is not enabled"):
        await MockExtractor().extract(
            ExtractionInput(
                filename="aadhaar.pdf",
                content_type="application/pdf",
                content=b"binary",
                document_type="aadhaar",
            )
        )


@pytest.mark.asyncio
async def test_gemini_without_key_logs_and_raises(caplog) -> None:
    settings = Settings(gemini_api_key=None)
    with caplog.at_level(logging.ERROR), pytest.raises(
        ExtractionError, match="ENV_REQUIRED"
    ):
        await GeminiExtractor(settings=settings).extract(
            ExtractionInput(
                filename="aadhaar.pdf",
                content_type="application/pdf",
                content=b"binary",
                document_type="aadhaar",
            )
        )
    assert "GEMINI_API_KEY is not configured" in caplog.text


@pytest.mark.asyncio
async def test_gemini_returns_only_schema_fields_and_validates_dates() -> None:
    class FakeModels:
        async def generate_content(self, **kwargs):
            assert kwargs["model"] == "gemini-2.5-flash"
            return SimpleNamespace(
                parsed={
                    "fields": {
                        "owner_name": "Ravi Kumar",
                        "plot_identifier": "PL-42",
                        "land_ownership_date": "2018-10-01",
                        "address": None,
                        "invented": "ignored",
                    }
                },
                text=None,
            )

    class FakeAio:
        models = FakeModels()

    fake_client = SimpleNamespace(aio=FakeAio())
    settings = Settings(gemini_api_key="test-key")
    result = await GeminiExtractor(settings=settings, client=fake_client).extract(
        ExtractionInput(
            filename="land.pdf",
            content_type="application/pdf",
            content=b"binary",
            document_type="land_record",
        )
    )
    assert result.extractor == "gemini:gemini-2.5-flash"
    assert result.fields == {
        "owner_name": "Ravi Kumar",
        "plot_identifier": "PL-42",
        "land_ownership_date": "2018-10-01",
        "address": None,
    }


@pytest.mark.asyncio
async def test_gemini_invalid_extracted_date_becomes_unknown() -> None:
    class FakeModels:
        async def generate_content(self, **kwargs):
            return SimpleNamespace(
                parsed={"fields": {"name": "Asha", "dob": "not-a-date"}},
                text=None,
            )

    fake_client = SimpleNamespace(
        aio=SimpleNamespace(models=FakeModels())
    )
    result = await GeminiExtractor(
        settings=Settings(gemini_api_key="test-key"), client=fake_client
    ).extract(
        ExtractionInput(
            filename="aadhaar.png",
            content_type="image/png",
            content=b"binary",
            document_type="aadhaar",
        )
    )
    assert result.fields["dob"] is None
