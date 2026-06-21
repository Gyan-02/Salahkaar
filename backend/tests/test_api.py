from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import func, select

from app.models.analysis import Analysis
from app.models.citizen_profile import CitizenProfile
from app.models.document import Document
from app.schemas.common import ExtractionStatus
from app.schemas.document import ExtractionResult


def test_health_programs_and_openapi(api_client) -> None:
    client, _ = api_client
    assert client.get("/health").json()["status"] == "ok"
    programs = client.get("/programs")
    assert programs.status_code == 200
    assert [program["id"] for program in programs.json()] == [
        "pm-kisan",
        "nmmss",
        "ayushman-bharat-pm-jay",
    ]
    assert client.get("/programs/not-real").status_code == 404
    assert len(client.get("/openapi.json").json()["paths"]) == 14


def test_master_analysis_and_demo_cases_persist(api_client, mock_cases) -> None:
    client, session_factory = api_client
    expected_document_count = 0
    for case in mock_cases:
        request = {
            "program_id": case["program_id"],
            "documents": case["documents"],
            "answers": case.get("answers", {}),
            "document_quality": case.get("document_quality", []),
        }
        response = client.post("/analysis/run", json=request)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["readiness_score"] == case["expected_readiness_score"]
        assert [action["action_id"] for action in result["actions"]] == case[
            "expected_action_ids"
        ]
        demo = client.post(f"/demo/run/{case['id']}")
        assert demo.status_code == 200, demo.text
        assert demo.json()["case_id"] == case["id"]
        expected_document_count += len(case["documents"]) * 2

    with session_factory() as session:
        assert session.scalar(select(func.count(Document.id))) == expected_document_count
        assert session.scalar(select(func.count(CitizenProfile.id))) == 8
        assert session.scalar(select(func.count(Analysis.id))) == 8


def test_pmjay_pending_contract_on_all_downstream_routes(api_client, mock_cases) -> None:
    client, _ = api_client
    case = next(case for case in mock_cases if case["program_id"] == "ayushman-bharat-pm-jay")
    request = {
        "program_id": case["program_id"],
        "documents": case["documents"],
        "answers": {},
    }
    result = client.post("/analysis/run", json=request).json()
    assert {key: result[key] for key in (
        "status", "eligible", "readiness_score", "risk_level", "risk_reason", "blockers", "actions"
    )} == {
        "status": "OFFICIAL_RULES_PENDING",
        "eligible": None,
        "readiness_score": None,
        "risk_level": "PENDING",
        "risk_reason": "POLICY_INCOMPLETE",
        "blockers": [],
        "actions": [],
    }
    assert client.post("/eligibility/check", json=request).json()["status"] == "OFFICIAL_RULES_PENDING"
    assert client.post("/readiness/check", json=request).json()["readiness_score"] is None
    assert client.post("/risk/check", json=request).json()["risk_level"] == "PENDING"
    assert client.post("/risk/check", json=request).json()["risk_reason"] == "POLICY_INCOMPLETE"
    assert client.post("/action-plan", json=request).json()["actions"] == []


def test_questions_and_contradictions_routes(api_client, mock_cases) -> None:
    client, _ = api_client
    case = next(case for case in mock_cases if case["program_id"] == "pm-kisan")
    answers = dict(case["answers"])
    del answers["paid_income_tax_last_assessment_year"]
    request = {
        "program_id": case["program_id"],
        "documents": case["documents"],
        "answers": answers,
    }
    questions = client.post("/questions/generate", json=request).json()["questions"]
    assert [question["field"] for question in questions] == [
        "paid_income_tax_last_assessment_year"
    ]
    documents = [
        {
            "document_type": document["document_type"],
            "document_id": document["filename"],
            "fields": document["fields"],
        }
        for document in case["documents"]
    ]
    issues = client.post(
        "/contradictions/check", json={"documents": documents}
    ).json()["issues"]
    assert [issue["code"] for issue in issues] == ["cross_document_name_mismatch"]


def test_upload_extract_and_delete_on_success(
    api_client, tmp_path, monkeypatch
) -> None:
    client, session_factory = api_client
    monkeypatch.setattr(
        "app.api.routes.documents.get_settings",
        lambda: SimpleNamespace(upload_path=tmp_path, max_upload_bytes=10_000),
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("land.pdf", b"binary", "application/pdf")},
    )
    token = upload.json()["upload_token"]
    path = tmp_path / token
    assert path.exists()
    response = client.post(
        "/documents/extract",
        json={
            "upload_token": token,
            "document_type": "land_record",
            "mock_fields": {
                "owner_name": "Ravi Kumar",
                "land_ownership_date": "2018-10-01",
            },
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["extraction"]["fields"]["land_ownership_date"] == "2018-10-01"
    assert not path.exists()
    with session_factory() as session:
        persisted = session.scalar(select(Document).order_by(Document.created_at.desc()))
        assert persisted is not None
        assert persisted.extracted_fields["land_ownership_date"] == "2018-10-01"


def test_upload_deleted_when_extraction_fails(api_client, tmp_path, monkeypatch) -> None:
    client, _ = api_client
    monkeypatch.setattr(
        "app.api.routes.documents.get_settings",
        lambda: SimpleNamespace(upload_path=tmp_path, max_upload_bytes=10_000),
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("land.pdf", b"binary", "application/pdf")},
    )
    token = upload.json()["upload_token"]
    path = tmp_path / token
    response = client.post(
        "/documents/extract",
        json={"upload_token": token, "document_type": "land_record"},
    )
    assert response.status_code == 422
    assert not path.exists()


def test_live_extraction_requires_explicit_external_processing_consent(
    api_client, tmp_path, monkeypatch
) -> None:
    client, _ = api_client
    monkeypatch.setattr(
        "app.api.routes.documents.get_settings",
        lambda: SimpleNamespace(
            upload_path=tmp_path,
            max_upload_bytes=10_000,
            use_gemini_extractor=True,
        ),
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("aadhaar.png", b"binary", "image/png")},
    )
    token = upload.json()["upload_token"]
    response = client.post(
        "/documents/extract",
        json={"upload_token": token, "document_type": "aadhaar"},
    )
    assert response.status_code == 422
    assert "Consent is required" in response.json()["detail"]
    assert not (tmp_path / token).exists()


def test_live_upload_routes_to_gemini_and_persists_extracted_fields(
    api_client, tmp_path, monkeypatch
) -> None:
    client, session_factory = api_client
    settings = SimpleNamespace(
        upload_path=tmp_path,
        max_upload_bytes=10_000,
        use_gemini_extractor=True,
    )
    monkeypatch.setattr(
        "app.api.routes.documents.get_settings", lambda: settings
    )

    class FakeGeminiExtractor:
        SUPPORTED_CONTENT_TYPES = {
            "application/pdf", "image/jpeg", "image/png", "image/webp"
        }

        def __init__(self, settings):
            assert settings.use_gemini_extractor is True

        async def extract(self, document):
            assert document.content == b"real-image-bytes"
            return ExtractionResult(
                document_type=document.document_type,
                fields={"name": "Asha Devi", "dob": "2012-04-06"},
                extractor="gemini:gemini-2.5-flash",
                status=ExtractionStatus.SUCCEEDED,
            )

    monkeypatch.setattr(
        "app.api.routes.documents.GeminiExtractor", FakeGeminiExtractor
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("aadhaar.png", b"real-image-bytes", "image/png")},
    )
    token = upload.json()["upload_token"]
    response = client.post(
        "/documents/extract",
        json={
            "upload_token": token,
            "document_type": "aadhaar",
            "consent_to_external_processing": True,
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["extraction"]["fields"]["name"] == "Asha Devi"
    assert not (tmp_path / token).exists()
    with session_factory() as session:
        persisted = session.scalar(
            select(Document).order_by(Document.created_at.desc())
        )
        assert persisted is not None
        assert persisted.extractor == "gemini:gemini-2.5-flash"


def test_unknown_demo_case_returns_404(api_client) -> None:
    client, _ = api_client
    assert client.post("/demo/run/not-real").status_code == 404
