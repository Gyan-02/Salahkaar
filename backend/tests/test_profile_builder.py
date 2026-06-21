from app.engines.profile_builder import ProfileBuilder
from app.schemas.profile import ProfileDocument


def test_profile_builder_preserves_provenance_and_conflict(
    profile_builder: ProfileBuilder,
) -> None:
    profile = profile_builder.build(
        [
            ProfileDocument(
                document_type="aadhaar",
                document_id="aadhaar-1",
                fields={"name": "Ravi Kumar", "address": "Patna"},
            ),
            ProfileDocument(
                document_type="land_record",
                document_id="land-1",
                fields={"owner_name": "Ravi Kamar", "address": "Patna"},
            ),
        ]
    )
    assert profile.fields["name"].conflicted is True
    assert profile.fields["name"].value is None
    assert [(value.value, value.source) for value in profile.fields["name"].values] == [
        ("Ravi Kumar", "aadhaar"),
        ("Ravi Kamar", "land_record"),
    ]
    assert profile.fields["address"].value == "Patna"
    assert len(profile.conflicts) == 1


def test_profile_builder_normalizes_only_for_comparison(
    profile_builder: ProfileBuilder,
) -> None:
    profile = profile_builder.build(
        [
            ProfileDocument(document_type="aadhaar", fields={"name": " Ravi  Kumar "}),
            ProfileDocument(document_type="bank_passbook", fields={"name": "ravi kumar"}),
        ]
    )
    assert profile.fields["name"].conflicted is False
    assert profile.fields["name"].value == " Ravi  Kumar "
    assert len(profile.fields["name"].values) == 2


def test_land_ownership_date_is_structurally_accepted(
    profile_builder: ProfileBuilder,
) -> None:
    profile = profile_builder.build(
        [
            ProfileDocument(
                document_type="land_record",
                fields={"land_ownership_date": "2018-10-01"},
            )
        ]
    )
    assert profile.fields["land_ownership_date"].value == "2018-10-01"
    assert profile.fields["land_ownership_date"].source == "land_record"


def test_profile_builder_reports_missing_required_fields(
    profile_builder: ProfileBuilder,
) -> None:
    profile = profile_builder.build(
        [ProfileDocument(document_type="aadhaar", fields={"name": "Asha Devi"})],
        required_fields=["name", "paid_income_tax_last_assessment_year"],
    )
    assert profile.missing_fields == ["paid_income_tax_last_assessment_year"]

