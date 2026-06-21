import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  CircleHelp,
  ClipboardCheck,
  ExternalLink,
  FileSearch,
  ShieldAlert,
} from "lucide-react";
import { Link } from "react-router-dom";
import type {
  AnalysisIssue,
  AnalysisResult,
  OfficialReference,
  RiskReason,
} from "../types";

export const riskCopy: Record<RiskReason, string> = {
  POLICY_INCOMPLETE:
    "We cannot fully assess the application because verified policy coverage is incomplete.",
  DOCUMENT_BLOCKERS:
    "We found document or information issues the applicant may be able to correct.",
  ELIGIBILITY_FAILURE:
    "A currently enabled verified eligibility rule was not satisfied.",
  MULTIPLE_FACTORS:
    "More than one category applies, such as incomplete policy coverage plus document blockers.",
};

function statusContent(result: AnalysisResult) {
  if (result.status === "OFFICIAL_RULES_PENDING")
    return {
      tone: "pending",
      icon: ShieldAlert,
      label: "Criteria Pending Verification",
      text: "This scheme cannot yet be assessed using complete verified official rules.",
    };
  if (result.eligible === true)
    return {
      tone: "success",
      icon: CheckCircle2,
      label: "Eligible",
      text: "The analysis service explicitly confirmed eligibility.",
    };
  if (result.eligible === false)
    return {
      tone: "danger",
      icon: AlertCircle,
      label: "A verified eligibility rule was not satisfied",
      text: "Review the information below. This result is based only on currently enabled verified rules.",
    };
  if (result.status === "PARTIAL_RULES_EVALUATED")
    return {
      tone: "partial",
      icon: ClipboardCheck,
      label: "No failure found in the currently verified rules",
      text: "Final eligibility cannot yet be confirmed.",
    };
  return {
    tone: "info",
    icon: CircleHelp,
    label: "More information is needed",
    text: "Complete the requested information before this application can be assessed.",
  };
}

export function SourceReference({
  reference,
}: {
  reference: OfficialReference;
}) {
  return (
    <div className="source-reference">
      <div className="source-kicker">
        <BookOpen size={16} /> Supported by official scheme text
      </div>
      <blockquote>{reference.text}</blockquote>
      <div className="source-meta">
        <span>{reference.section_reference}</span>
        <a href={reference.source_url} target="_blank" rel="noreferrer">
          Open official source <ExternalLink size={14} />
        </a>
      </div>
      <details>
        <summary>Technical details</summary>
        <p>Retrieval score: {reference.score.toFixed(2)}</p>
      </details>
    </div>
  );
}

function Evidence({ issue }: { issue: AnalysisIssue }) {
  if (!issue.evidence.length) return null;
  return (
    <div className="evidence">
      <strong>
        <FileSearch size={15} /> Detected from supplied documents
      </strong>
      {issue.evidence.map((item, index) => (
        <dl key={index}>
          {Object.entries(item).map(([key, value]) => (
            <div key={key}>
              <dt>{key.replaceAll("_", " ")}</dt>
              <dd>
                {typeof value === "object"
                  ? JSON.stringify(value)
                  : String(value)}
              </dd>
            </div>
          ))}
        </dl>
      ))}
    </div>
  );
}

export function IssueCard({ issue }: { issue: AnalysisIssue }) {
  return (
    <article className="issue-card">
      <div className="issue-heading">
        <span className={`severity severity-${issue.severity.toLowerCase()}`}>
          {issue.severity}
        </span>
        <span>{issue.category.replaceAll("_", " ")}</span>
      </div>
      <h3>{issue.message}</h3>
      <Evidence issue={issue} />
      {issue.official_reference && (
        <SourceReference reference={issue.official_reference} />
      )}
    </article>
  );
}

export function ResultView({
  result,
  onStartOver,
}: {
  result: AnalysisResult;
  onStartOver?: () => void;
}) {
  const status = statusContent(result);
  const StatusIcon = status.icon;
  const pending = result.status === "OFFICIAL_RULES_PENDING";
  const allIssues = [
    ...result.issues,
    ...result.blockers.filter(
      (blocker) => !result.issues.some((issue) => issue.code === blocker.code),
    ),
  ];
  return (
    <main className="result-page page-shell" aria-live="polite">
      <div className="result-topline">
        <div>
          <span className="eyebrow">Your local analysis</span>
          <h1>Readiness result</h1>
        </div>
        <span className="local-pill">Mock · local</span>
      </div>
      <section className={`status-banner status-${status.tone}`}>
        <StatusIcon aria-hidden="true" />
        <div>
          <p className="status-overline">Assessment status</p>
          <h2>{status.label}</h2>
          <p>{status.text}</p>
        </div>
      </section>
      {!pending && result.status === "PARTIAL_RULES_EVALUATED" && (
        <div className="policy-note">
          <ShieldAlert size={20} />
          <p>
            <strong>Policy coverage is incomplete.</strong> The result covers
            currently verified rules only.
          </p>
        </div>
      )}
      <div className="result-grid">
        {result.readiness_score !== null && (
          <section className="score-card">
            <span className="section-icon">
              <ClipboardCheck />
            </span>
            <p className="card-label">Application readiness</p>
            <div className="score-row">
              <strong>{result.readiness_score}</strong>
              <span>/ 100</span>
            </div>
            <progress max="100" value={result.readiness_score}>
              {result.readiness_score}%
            </progress>
            <p>
              Readiness reflects document and information preparation. It is not
              an eligibility probability.
            </p>
          </section>
        )}
        {!pending && result.risk_reason && (
          <section className="risk-card">
            <span className="section-icon">
              <ShieldAlert />
            </span>
            <p className="card-label">Why this result needs attention</p>
            <h2>{result.risk_reason.replaceAll("_", " ")}</h2>
            <p>{riskCopy[result.risk_reason]}</p>
            <span
              className={`risk-level risk-${result.risk_level.toLowerCase()}`}
            >
              {result.risk_level} attention
            </span>
          </section>
        )}
      </div>
      {!pending && allIssues.length > 0 && (
        <section className="section-block">
          <div className="section-title">
            <span className="eyebrow">What we found</span>
            <h2>Issues and blockers</h2>
          </div>
          <div className="issue-list">
            {allIssues.map((issue) => (
              <IssueCard
                key={`${issue.code}-${issue.category}`}
                issue={issue}
              />
            ))}
          </div>
        </section>
      )}
      {!pending && result.actions.length > 0 && (
        <section className="section-block">
          <div className="section-title">
            <span className="eyebrow">Next best steps</span>
            <h2>Prioritised actions</h2>
          </div>
          <ol className="action-list">
            {[...result.actions]
              .sort((a, b) => a.priority - b.priority)
              .map((action) => (
                <li key={action.action_id}>
                  <span>{action.priority}</span>
                  <div>
                    <h3>{action.instruction}</h3>
                    <p>{action.reason}</p>
                  </div>
                  <ArrowRight aria-hidden="true" />
                </li>
              ))}
          </ol>
        </section>
      )}
      {!pending && result.questions.length > 0 && (
        <section className="section-block">
          <div className="section-title">
            <span className="eyebrow">Information needed</span>
            <h2>Follow-up questions</h2>
          </div>
          <ul className="question-list">
            {result.questions.map((question) => (
              <li key={question.field}>{question.question}</li>
            ))}
          </ul>
        </section>
      )}
      {!pending && result.explanations.length > 0 && (
        <section className="explanation-panel">
          <h2>How this result was calculated</h2>
          <ul>
            {result.explanations.map((text, index) => (
              <li key={index}>{text}</li>
            ))}
          </ul>
        </section>
      )}
      <div className="result-actions">
        {onStartOver && (
          <button className="button button-primary" onClick={onStartOver}>
            Check another application
          </button>
        )}
        <Link className="button button-secondary" to="/guidelines">
          Look up official guidelines
        </Link>
      </div>
    </main>
  );
}
