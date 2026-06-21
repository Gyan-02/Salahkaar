# Tracked MVP follow-ups

## DATE_NORMALIZATION_BEFORE_CUTOFF_RULE

Status: **required before enabling any PM-KISAN land-ownership cutoff rule**.

# OFFICIAL_SOURCE_REQUIRED

Current behavior:

- Extracted date-typed fields, including `land_ownership_date`, retain the extractor's raw value.
- ISO `YYYY-MM-DD` values work in current expiry and ordered-rule comparisons because those engines parse ISO dates at comparison time.
- Other representations such as `01/02/2019`, `01-02-2019`, localized month names, or OCR-damaged values are not normalized and may be ambiguous.

Required implementation before the cutoff rule is enabled:

- Normalize date-typed extracted fields to canonical ISO-8601 `YYYY-MM-DD` immediately after extraction and before profile construction.
- Preserve the raw extracted value alongside the normalized value for provenance and explanation.
- Reject or request confirmation for ambiguous day/month values rather than guessing.
- Add tests covering ISO input, Indian `DD-MM-YYYY`, invalid calendar dates, ambiguous dates, and cross-document comparison.
- Enable the cutoff rule only after both date normalization and the official cutoff/inheritance policy are verified.
