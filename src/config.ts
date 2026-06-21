import type { ProgramId } from "./types";

export interface QuestionConfig {
  field: string;
  label: string;
  type: "boolean" | "number";
}
export interface DocumentField {
  key: string;
  label: string;
  type: "text" | "number" | "date" | "list";
}
export interface DocumentConfig {
  type: string;
  label: string;
  fields: DocumentField[];
}
export interface SchemeConfig {
  id: ProgramId;
  shortName: string;
  name: string;
  description: string;
  eyebrow: string;
  pending?: boolean;
  questions: QuestionConfig[];
  documents: DocumentConfig[];
}

export const schemes: SchemeConfig[] = [
  {
    id: "pm-kisan",
    shortName: "PM-KISAN",
    name: "PM-KISAN",
    eyebrow: "Farmer family support",
    description:
      "Check readiness using the currently verified rules and your supplied records.",
    questions: [
      {
        field: "family_owns_cultivable_land",
        label: "Does your farmer family own cultivable land?",
        type: "boolean",
      },
      {
        field: "institutional_landholder",
        label: "Is the land held by an institution?",
        type: "boolean",
      },
      {
        field: "holds_excluded_public_office",
        label:
          "Does any family member fall within the listed public-office categories?",
        type: "boolean",
      },
      {
        field: "excluded_government_employee",
        label:
          "Does any family member fall within the listed government-employee categories?",
        type: "boolean",
      },
      {
        field: "excluded_high_pensioner",
        label:
          "Does any family member fall within the listed pension category?",
        type: "boolean",
      },
      {
        field: "paid_income_tax_last_assessment_year",
        label:
          "Did any family member pay income tax in the last assessment year?",
        type: "boolean",
      },
      {
        field: "practicing_registered_professional",
        label:
          "Is any family member a listed registered professional who is actively practising?",
        type: "boolean",
      },
    ],
    documents: [
      {
        type: "aadhaar",
        label: "Identity record",
        fields: [
          { key: "name", label: "Name on identity record", type: "text" },
          { key: "dob", label: "Date of birth", type: "date" },
          { key: "address", label: "Address", type: "text" },
        ],
      },
      {
        type: "land_record",
        label: "Land record",
        fields: [
          { key: "owner_name", label: "Owner name", type: "text" },
          { key: "plot_identifier", label: "Plot identifier", type: "text" },
          { key: "land_ownership_date", label: "Ownership date", type: "date" },
          { key: "address", label: "Address", type: "text" },
        ],
      },
    ],
  },
  {
    id: "nmmss",
    shortName: "NMMSS",
    name: "National Means-cum-Merit Scholarship Scheme",
    eyebrow: "Student scholarship",
    description:
      "Review application readiness using the currently verified fresh-selection rules.",
    questions: [
      {
        field: "parental_annual_income",
        label: "What is the student's parental annual income from all sources?",
        type: "number",
      },
      {
        field: "entering_class",
        label: "Which class is the student entering for the fresh award?",
        type: "number",
      },
      {
        field: "attends_eligible_school_type",
        label:
          "Does the student attend a school type covered by the currently verified rule?",
        type: "boolean",
      },
      {
        field: "meets_class_7_marks_rule",
        label: "Does the student meet the Class VII marks rule?",
        type: "boolean",
      },
      {
        field: "passed_mat_sat_rule",
        label: "Does the student meet the combined MAT/SAT rule?",
        type: "boolean",
      },
      {
        field: "meets_class_8_marks_rule",
        label: "Does the student meet the Class VIII award-stage marks rule?",
        type: "boolean",
      },
      {
        field: "receives_other_central_scholarship",
        label:
          "Is the student receiving another Central Government scholarship?",
        type: "boolean",
      },
    ],
    documents: [
      {
        type: "aadhaar",
        label: "Identity record",
        fields: [
          { key: "name", label: "Student name", type: "text" },
          { key: "dob", label: "Date of birth", type: "date" },
        ],
      },
      {
        type: "bank_passbook",
        label: "Bank passbook",
        fields: [
          { key: "name", label: "Account holder name", type: "text" },
          { key: "ifsc", label: "IFSC", type: "text" },
        ],
      },
      {
        type: "income_certificate",
        label: "Income certificate",
        fields: [
          { key: "name", label: "Name on certificate", type: "text" },
          {
            key: "annual_income",
            label: "Annual income shown",
            type: "number",
          },
          { key: "issue_date", label: "Issue date", type: "date" },
          { key: "expiry_date", label: "Expiry date", type: "date" },
        ],
      },
    ],
  },
  {
    id: "ayushman-bharat-pm-jay",
    shortName: "PM-JAY",
    name: "Ayushman Bharat PM-JAY",
    eyebrow: "Health coverage",
    description:
      "Official Bihar eligibility criteria are still being verified for this demo.",
    pending: true,
    questions: [],
    documents: [
      {
        type: "family_record",
        label: "Family record",
        fields: [
          {
            key: "family_members",
            label: "Family member names (comma-separated)",
            type: "list",
          },
          { key: "address", label: "Address", type: "text" },
        ],
      },
    ],
  },
];

export const schemeById = Object.fromEntries(
  schemes.map((scheme) => [scheme.id, scheme]),
) as Record<ProgramId, SchemeConfig>;
