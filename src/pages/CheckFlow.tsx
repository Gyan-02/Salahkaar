import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronRight,
  FileText,
  LoaderCircle,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { ResultView } from "../components/ResultView";
import { DocumentUpload } from "../components/DocumentUpload";
import {
  schemeById,
  schemes,
  type DocumentConfig,
  type SchemeConfig,
} from "../config";
import type {
  AnalysisDocument,
  AnalysisRequest,
  AnalysisResult,
  ProgramId,
} from "../types";

type AnswerState = Record<string, boolean | number | "">;
type DocumentState = Record<string, Record<string, string>>;

function emptyDocuments(scheme: SchemeConfig): DocumentState {
  return Object.fromEntries(
    scheme.documents.map((doc) => [
      doc.type,
      Object.fromEntries(doc.fields.map((field) => [field.key, ""])),
    ]),
  );
}

function Stepper({ step }: { step: number }) {
  return (
    <ol className="stepper" aria-label="Readiness check progress">
      {["Choose scheme", "Your information", "Review"].map((label, index) => (
        <li key={label} className={step >= index + 1 ? "current" : ""}>
          <span>{step > index + 1 ? <Check /> : index + 1}</span>
          <p>{label}</p>
        </li>
      ))}
    </ol>
  );
}

function SchemeStep({ onChoose }: { onChoose: (id: ProgramId) => void }) {
  return (
    <section>
      <div className="flow-heading">
        <span className="eyebrow">Step 1 of 3</span>
        <h1>Choose a benefit scheme</h1>
        <p>
          We’ll tailor the questions and document sections to your selection.
        </p>
      </div>
      <div className="select-scheme-list">
        {schemes.map((scheme) => (
          <button key={scheme.id} onClick={() => onChoose(scheme.id)}>
            <span className="scheme-monogram">
              {scheme.shortName.slice(0, 2)}
            </span>
            <span>
              <strong>{scheme.name}</strong>
              <small>{scheme.description}</small>
              {scheme.pending && <em>Criteria verification pending</em>}
            </span>
            <ChevronRight />
          </button>
        ))}
      </div>
    </section>
  );
}

function BooleanField({
  name,
  label,
  value,
  onChange,
}: {
  name: string;
  label: string;
  value: boolean | "";
  onChange: (value: boolean) => void;
}) {
  return (
    <fieldset className="boolean-field">
      <legend>{label}</legend>
      <div>
        <label>
          <input
            required
            type="radio"
            name={name}
            checked={value === true}
            onChange={() => onChange(true)}
          />{" "}
          Yes
        </label>
        <label>
          <input
            required
            type="radio"
            name={name}
            checked={value === false}
            onChange={() => onChange(false)}
          />{" "}
          No
        </label>
      </div>
    </fieldset>
  );
}

function DocumentSection({
  config,
  values,
  onChange,
  onExtracted,
}: {
  config: DocumentConfig;
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onExtracted: (fields: Record<string, unknown>) => void;
}) {
  return (
    <fieldset className="document-section">
      <legend>
        <FileText /> {config.label}
      </legend>
      <p>
        Upload a document for Gemini extraction or enter its fields manually.
        You can review and correct every extracted value.
      </p>
      <DocumentUpload documentType={config.type} onExtracted={onExtracted} />
      <div className="field-grid">
        {config.fields.map((field) => (
          <label key={field.key}>
            {field.label}
            <input
              type={field.type === "list" ? "text" : field.type}
              value={values[field.key]}
              onChange={(e) => onChange(field.key, e.target.value)}
              placeholder={
                field.type === "list" ? "Name one, Name two" : undefined
              }
            />
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function buildRequest(
  scheme: SchemeConfig,
  answers: AnswerState,
  documents: DocumentState,
): AnalysisRequest {
  const payloadDocs: AnalysisDocument[] = scheme.documents.flatMap((doc) => {
    const fields = Object.fromEntries(
      doc.fields.flatMap((field) => {
        const raw = documents[doc.type]?.[field.key]?.trim();
        if (!raw) return [];
        const value: unknown =
          field.type === "number"
            ? Number(raw)
            : field.type === "list"
              ? raw
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean)
              : raw;
        return [[field.key, value]];
      }),
    );
    return Object.keys(fields).length
      ? [
          {
            document_type: doc.type,
            filename: `local-${doc.type}.json`,
            fields,
          },
        ]
      : [];
  });
  return {
    program_id: scheme.id,
    answers: Object.fromEntries(
      Object.entries(answers).filter(([, value]) => value !== ""),
    ),
    documents: payloadDocs,
    document_quality: [],
  };
}

function ReviewValue({ value }: { value: unknown }) {
  return (
    <>
      {typeof value === "boolean"
        ? value
          ? "Yes"
          : "No"
        : Array.isArray(value)
          ? value.join(", ")
          : String(value)}
    </>
  );
}

export function CheckFlow() {
  const [params, setParams] = useSearchParams();
  const initial = params.get("scheme") as ProgramId | null;
  const [schemeId, setSchemeId] = useState<ProgramId | null>(
    initial && schemeById[initial] ? initial : null,
  );
  const [step, setStep] = useState(initial && schemeById[initial] ? 2 : 1);
  const [answers, setAnswers] = useState<AnswerState>({});
  const [documents, setDocuments] = useState<DocumentState>(
    initial && schemeById[initial] ? emptyDocuments(schemeById[initial]) : {},
  );
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scheme = schemeId ? schemeById[schemeId] : null;
  const payload = useMemo(
    () => (scheme ? buildRequest(scheme, answers, documents) : null),
    [scheme, answers, documents],
  );
  const choose = (id: ProgramId) => {
    setSchemeId(id);
    setAnswers({});
    setDocuments(emptyDocuments(schemeById[id]));
    setParams({ scheme: id });
    setStep(2);
  };
  const submitInfo = (event: FormEvent) => {
    event.preventDefault();
    const unanswered = scheme?.questions.filter(
      (question) =>
        answers[question.field] === undefined || answers[question.field] === "",
    );
    if (unanswered?.length) {
      setError(
        `Answer all applicant questions before continuing. ${unanswered.length} answer${unanswered.length === 1 ? " is" : "s are"} still missing.`,
      );
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (!payload?.documents.length) {
      setError(
        "Upload a document or enter information from at least one document before continuing.",
      );
      return;
    }
    setError(null);
    setStep(3);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const run = async () => {
    if (!payload) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await api.runAnalysis(payload));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "The analysis could not be completed.",
      );
    } finally {
      setLoading(false);
    }
  };
  const reset = () => {
    setResult(null);
    setSchemeId(null);
    setAnswers({});
    setDocuments({});
    setStep(1);
    setParams({});
    setError(null);
  };
  if (result) return <ResultView result={result} onStartOver={reset} />;
  return (
    <main className="flow-page">
      <div className="page-shell">
        <Stepper step={step} />
        {error && (
          <div className="error-banner" role="alert">
            <p>{error}</p>
            {step === 3 && (
              <button onClick={() => void run()}>Retry analysis</button>
            )}
          </div>
        )}
        {step === 1 && <SchemeStep onChoose={choose} />}
        {step === 2 && scheme && (
          <form onSubmit={submitInfo}>
            <div className="flow-heading">
              <span className="eyebrow">Step 2 of 3 · {scheme.shortName}</span>
              <h1>Tell us what you have</h1>
              <p>
                Upload your documents or enter the details below. You can review
                and correct everything before the readiness analysis.
              </p>
            </div>
            {scheme.questions.length > 0 && (
              <section className="form-card">
                <div className="form-card-heading">
                  <span>01</span>
                  <div>
                    <h2>Applicant information</h2>
                    <p>Answer the scheme-specific questions below.</p>
                  </div>
                </div>
                <div className="question-stack">
                  {scheme.questions.map((question) =>
                    question.type === "boolean" ? (
                      <BooleanField
                        key={question.field}
                        name={question.field}
                        label={question.label}
                        value={(answers[question.field] ?? "") as boolean | ""}
                        onChange={(value) =>
                          setAnswers({ ...answers, [question.field]: value })
                        }
                      />
                    ) : (
                      <label className="number-field" key={question.field}>
                        {question.label}
                        <input
                          required
                          type="number"
                          value={
                            (answers[question.field] as number | undefined) ??
                            ""
                          }
                          onChange={(e) =>
                            setAnswers({
                              ...answers,
                              [question.field]:
                                e.target.value === ""
                                  ? ""
                                  : Number(e.target.value),
                            })
                          }
                        />
                      </label>
                    ),
                  )}
                </div>
              </section>
            )}
            <section className="form-card">
              <div className="form-card-heading">
                <span>{scheme.questions.length ? "02" : "01"}</span>
                <div>
                  <h2>Document information</h2>
                  <p>
                    These sections match document types supported by the
                    analysis service.
                  </p>
                </div>
              </div>
              {scheme.documents.map((doc) => (
                <DocumentSection
                  key={doc.type}
                  config={doc}
                  values={documents[doc.type]}
                  onChange={(key, value) =>
                    setDocuments({
                      ...documents,
                      [doc.type]: { ...documents[doc.type], [key]: value },
                    })
                  }
                  onExtracted={(fields) =>
                    setDocuments({
                      ...documents,
                      [doc.type]: {
                        ...documents[doc.type],
                        ...Object.fromEntries(
                          Object.entries(fields).map(([key, value]) => [
                            key,
                            Array.isArray(value)
                              ? value.join(", ")
                              : value === null || value === undefined
                                ? ""
                                : String(value),
                          ]),
                        ),
                      },
                    })
                  }
                />
              ))}
            </section>
            <div className="flow-buttons">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setStep(1)}
              >
                <ArrowLeft /> Back
              </button>
              <button className="button button-primary">
                Review information <ArrowRight />
              </button>
            </div>
          </form>
        )}
        {step === 3 && scheme && payload && (
          <section>
            <div className="flow-heading">
              <span className="eyebrow">Step 3 of 3 · {scheme.shortName}</span>
              <h1>Review before analysis</h1>
              <p>
                This is a mock, local analysis. Check that the information below
                matches what you meant to enter.
              </p>
            </div>
            <div className="review-notice">
              <ShieldCheck />
              <p>
                <strong>Readiness guidance only.</strong> This is not an
                application submission or an official approval decision.
              </p>
            </div>
            {Object.keys(payload.answers).length > 0 && (
              <section className="review-card">
                <h2>Applicant information</h2>
                <dl>
                  {scheme.questions
                    .filter((q) => q.field in payload.answers)
                    .map((q) => (
                      <div key={q.field}>
                        <dt>{q.label}</dt>
                        <dd>
                          <ReviewValue value={payload.answers[q.field]} />
                        </dd>
                      </div>
                    ))}
                </dl>
              </section>
            )}
            <section className="review-card">
              <h2>Document information</h2>
              {payload.documents.map((doc) => (
                <div className="review-document" key={doc.document_type}>
                  <h3>
                    {
                      scheme.documents.find(
                        (item) => item.type === doc.document_type,
                      )?.label
                    }
                  </h3>
                  <dl>
                    {Object.entries(doc.fields).map(([key, value]) => (
                      <div key={key}>
                        <dt>
                          {scheme.documents
                            .flatMap((d) => d.fields)
                            .find((f) => f.key === key)?.label ?? key}
                        </dt>
                        <dd>
                          <ReviewValue value={value} />
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              ))}
            </section>
            <div className="flow-buttons">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setStep(2)}
              >
                <ArrowLeft /> Edit information
              </button>
              <button
                className="button button-primary"
                onClick={() => void run()}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <LoaderCircle className="spin" /> Running local analysis…
                  </>
                ) : (
                  <>
                    Run readiness analysis <ArrowRight />
                  </>
                )}
              </button>
            </div>
            <button className="reset-link" onClick={reset}>
              <RotateCcw /> Start over
            </button>
          </section>
        )}
      </div>
    </main>
  );
}
