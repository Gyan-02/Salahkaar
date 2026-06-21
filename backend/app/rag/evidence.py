from typing import cast

from app.rag.embeddings import normalize_tokens
from app.rag.models import ProgramId, RetrievalStatus
from app.rag.retriever import GuidelineRetriever
from app.schemas.analysis import OfficialReference


# Explicit policy-evidence queries. Unlisted issue codes intentionally receive
# no reference: retrieval queries are never guessed or generated dynamically.
ISSUE_RETRIEVAL_QUERIES: dict[tuple[ProgramId, str], str] = {
    ("pm-kisan", "income_tax_exclusion"): "income tax exclusion",
    ("pm-kisan", "pmkisan_no_recent_income_tax"): "income tax exclusion",
    ("pm-kisan", "pmkisan_not_institutional"): "institutional land holders",
    ("pm-kisan", "pmkisan_no_excluded_public_office"): "constitutional posts ministers members",
    ("pm-kisan", "pmkisan_no_excluded_government_employee"): "government employees exclusion",
    ("pm-kisan", "pmkisan_no_excluded_high_pensioner"): "retired pensioners monthly pension",
    ("pm-kisan", "pmkisan_no_practicing_registered_professional"): "registered professionals exclusion",
    ("nmmss", "parental_income_limit"): "parental income limit",
    ("nmmss", "nmmss_income_limit"): "parental income limit",
    ("nmmss", "scholarship_continuation"): "continuation of scholarship",
    ("nmmss", "nmmss_entering_class_9"): "scholarship class IX",
    ("nmmss", "nmmss_eligible_school"): "eligible school types",
    ("nmmss", "nmmss_class_7_marks"): "class VII marks",
    ("nmmss", "nmmss_mat_sat"): "MAT SAT pass marks",
    ("nmmss", "nmmss_class_8_marks"): "class VIII marks",
    ("nmmss", "nmmss_single_central_scholarship"): "Central Government scholarship",
    ("nmmss", "expired_document"): "document validity",
    ("nmmss", "bank_account_holder_mismatch"): "bank account",
}

# Every group represents a required concept. At least one term from every group
# must occur in the retrieved clause before it can support the specific issue.
# This entailment-oriented gate is deliberately stricter than topic retrieval.
ISSUE_SUPPORT_TERM_GROUPS: dict[
    tuple[ProgramId, str], tuple[frozenset[str], ...]
] = {
    ("pm-kisan", "income_tax_exclusion"): (
        frozenset({"income"}), frozenset({"tax"}), frozenset({"paid"}),
    ),
    ("pm-kisan", "pmkisan_no_recent_income_tax"): (
        frozenset({"income"}), frozenset({"tax"}), frozenset({"paid"}),
    ),
    ("pm-kisan", "pmkisan_not_institutional"): (
        frozenset({"institutional"}), frozenset({"land", "landholder", "holders"}),
    ),
    ("pm-kisan", "pmkisan_no_excluded_public_office"): (
        frozenset({"constitutional", "minister", "ministers", "mayors"}),
        frozenset({"holders", "members", "chairpersons"}),
    ),
    ("pm-kisan", "pmkisan_no_excluded_government_employee"): (
        frozenset({"government"}), frozenset({"officers", "employees"}),
    ),
    ("pm-kisan", "pmkisan_no_excluded_high_pensioner"): (
        frozenset({"pensioners", "pension"}), frozenset({"10000"}),
    ),
    ("pm-kisan", "pmkisan_no_practicing_registered_professional"): (
        frozenset({"professionals"}), frozenset({"registered"}),
    ),
    ("nmmss", "parental_income_limit"): (
        frozenset({"parental"}), frozenset({"income"}),
    ),
    ("nmmss", "nmmss_income_limit"): (
        frozenset({"parental"}), frozenset({"income"}),
    ),
    ("nmmss", "scholarship_continuation"): (
        frozenset({"scholarship"}), frozenset({"continuation", "continuing"}),
    ),
    ("nmmss", "nmmss_entering_class_9"): (
        frozenset({"class"}), frozenset({"ix", "9"}),
    ),
    ("nmmss", "nmmss_eligible_school"): (
        frozenset({"school", "schools"}),
        frozenset({"government", "aided", "residential", "local"}),
    ),
    ("nmmss", "nmmss_class_7_marks"): (
        frozenset({"class"}), frozenset({"vii", "7"}), frozenset({"marks"}),
    ),
    ("nmmss", "nmmss_mat_sat"): (
        frozenset({"mat"}), frozenset({"sat"}), frozenset({"marks"}),
    ),
    ("nmmss", "nmmss_class_8_marks"): (
        frozenset({"class"}), frozenset({"viii", "8"}), frozenset({"marks"}),
    ),
    ("nmmss", "nmmss_single_central_scholarship"): (
        frozenset({"central"}), frozenset({"scholarship"}),
    ),
    ("nmmss", "expired_document"): (
        frozenset({"document"}),
        frozenset({"expired", "expiry", "valid", "validity"}),
    ),
    ("nmmss", "bank_account_holder_mismatch"): (
        frozenset({"name", "holder"}),
        frozenset({"match", "matching", "mismatch", "differ", "differs"}),
    ),
}


class RagOfficialReferenceResolver:
    """Resolve mapped issue codes to one verbatim official-source chunk."""

    def __init__(self, retriever: GuidelineRetriever) -> None:
        self.retriever = retriever
        self._cache: dict[tuple[str, str], OfficialReference | None] = {}

    def __call__(self, program_id: str, issue_code: str) -> OfficialReference | None:
        key = (program_id, issue_code)
        if key in self._cache:
            return self._cache[key]

        # PM-JAY is policy-pending and must never invoke RAG from analysis.
        if program_id == "ayushman-bharat-pm-jay":
            self._cache[key] = None
            return None

        if program_id not in {"pm-kisan", "nmmss"}:
            self._cache[key] = None
            return None

        program = cast(ProgramId, program_id)
        query = ISSUE_RETRIEVAL_QUERIES.get((program, issue_code))
        if query is None:
            self._cache[key] = None
            return None

        response = self.retriever.retrieve(
            program=program,
            query=query,
            top_n=1,
        )
        if response.status != RetrievalStatus.MATCH or not response.result:
            self._cache[key] = None
            return None

        chunk = response.result[0]
        support_groups = ISSUE_SUPPORT_TERM_GROUPS.get((program, issue_code))
        if support_groups is None or not self._supports_claim(
            chunk.text,
            chunk.section_reference,
            support_groups,
        ):
            self._cache[key] = None
            return None

        reference = OfficialReference(
            text=chunk.text,
            source_url=chunk.source_url,
            section_reference=chunk.section_reference,
            score=chunk.score,
        )
        self._cache[key] = reference
        return reference

    @staticmethod
    def _supports_claim(
        text: str,
        section_reference: str,
        required_groups: tuple[frozenset[str], ...],
    ) -> bool:
        source_terms = set(normalize_tokens(f"{section_reference} {text}"))
        return all(source_terms & group for group in required_groups)
