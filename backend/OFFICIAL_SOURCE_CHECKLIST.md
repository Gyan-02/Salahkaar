# OFFICIAL_SOURCE_REQUIRED

The supplied facts were reviewed on 2026-06-21. The environment could not fetch the government sites independently, so `source_audit.json` records which claims came from user-supplied primary-source text and which still rely on mirrors or observations.

## PM-KISAN

Captured as active rules from the supplied official homepage text:

- Cultivable-land family basis.
- Institutional-landholder exclusion.
- Listed public-office exclusions.
- Government/PSE/local-body employee exclusion with stated staff exceptions.
- Monthly pension threshold of Rs 10,000 with stated staff exceptions.
- Last-assessment-year income-tax exclusion.
- Listed registered practising-professional exclusion.

Still required:

- [ ] Original official operational-guideline PDF text for the precise family definition.
- [ ] Original PDF verification of the 2019-02-01 land cutoff and inheritance/succession treatment.
- [ ] Original official source for the NRI exclusion.
- [ ] Original official source for the self-declaration mechanism.
- [ ] Accepted land, identity, bank and other documents, mandatory fields, validity and verification rules.
- [ ] Current official active-status/effective-version confirmation.

Correction: Rs 10,000 is a monthly pension threshold in the supplied exclusion list. It is not a land-value threshold.

## NMMSS

Captured from the supplied official revised-guideline text:

- Rs 3,50,000 parental annual-income ceiling.
- Eligible/excluded school types and Class IX fresh-entry basis.
- Class VII/Class VIII marks and SC/ST relaxation.
- MAT/SAT structure and pass thresholds.
- Rs 12,000 annual scholarship amount.
- Continuation, promotion, one-scholarship, NSP, bank, conduct and discontinuation provisions as source facts.

Still required:

- [ ] Official extension, continuation order, Cabinet approval or revised guideline covering AY 2026-27.
- [ ] Official national/state source confirming the 31 August 2026 deadline.
- [ ] Official source for any 13-15 age band; it is not an active rule.
- [ ] Current fresh and renewal document/verification checklist.

`program_active` is `true` only as an observed operational fact and carries `# OFFICIAL_SOURCE_REQUIRED`; it is not represented as confirmed post-2026 policy authority.

## Ayushman Bharat PM-JAY

Captured from the supplied NHA page text:

- SECC 2011 rural deprivation and urban occupational basis, including state-database flexibility.
- No family-size, age or gender cap.
- Pre-existing-condition and portability context.
- Citizen Portal/14555 verification channels.
- SECC 2011 context is metadata only and is not treated as a complete eligibility rule.

Still required:

- Demo jurisdiction: Bihar.
- [ ] Official Bihar beneficiary database, mapping/version, and verification rules.
- [ ] Official accepted identity, household and verification-document checklist.
- [ ] Official exclusion list, if one exists; no third-party exclusions are encoded.
- [ ] Primary NHA/PM-JAY confirmation of any separate 70+ top-up provision.
- [ ] Current official active-status/effective-version confirmation.

## Document schema confirmation

# USER_ACTION_REQUIRED

Confirmed for the MVP: `land_record` contains `owner_name`, `plot_identifier`, `land_ownership_date`, and `address`; `family_record` contains `family_members` and `address`. `land_ownership_date` remains unused until the cutoff/inheritance rule is verified and enabled.
