import { ArrowRight, FlaskConical, LoaderCircle } from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "../api";
import { ResultView } from "../components/ResultView";
import type { AnalysisResult } from "../types";

export const demoCases = [
  {
    id: "pm-kisan-name-land-mismatch",
    scheme: "PM-KISAN",
    title: "Name mismatch",
    description: "Identity and land records carry different spellings.",
  },
  {
    id: "pm-kisan-clean-readiness",
    scheme: "PM-KISAN",
    title: "Clean readiness",
    description: "Currently verified rules pass and records align.",
  },
  {
    id: "nmmss-expired-income-bank-name",
    scheme: "NMMSS",
    title: "Bank mismatch + expired record",
    description: "Two correctable document issues appear together.",
  },
  {
    id: "pm-jay-family-composition-mismatch",
    scheme: "PM-JAY",
    title: "Family-record conflict",
    description: "A document conflict while policy criteria remain pending.",
  },
];

export function DemoCases() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const run = async (id: string) => {
    setLoading(id);
    setError(null);
    try {
      setResult(await api.runDemo(id));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "The demo could not be run.",
      );
    } finally {
      setLoading(null);
    }
  };
  if (result)
    return <ResultView result={result} onStartOver={() => setResult(null)} />;
  return (
    <main className="page-shell interior-page">
      <div className="page-intro">
        <span className="eyebrow">
          <FlaskConical size={15} /> Synthetic demo data
        </span>
        <h1>See Salahkaar in action</h1>
        <p>
          Explore ready-made sample applications below. Each case is analysed in
          real time so you can see exactly how Salahkaar evaluates documents,
          checks eligibility, and flags issues.
        </p>
      </div>
      {error && (
        <div className="error-banner" role="alert">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      <div className="demo-grid">
        {demoCases.map((demo, index) => (
          <article className="demo-card" key={demo.id}>
            <span className="demo-number">0{index + 1}</span>
            <span className="program-tag">{demo.scheme}</span>
            <h2>{demo.title}</h2>
            <p>{demo.description}</p>
            <button onClick={() => run(demo.id)} disabled={loading !== null}>
              {loading === demo.id ? (
                <>
                  <LoaderCircle className="spin" /> Running local analysis…
                </>
              ) : (
                <>
                  Run this case <ArrowRight />
                </>
              )}
            </button>
          </article>
        ))}
      </div>
      <p className="demo-disclaimer">
        All people and records in these cases are synthetic. Demo outputs are
        not official decisions.
      </p>
    </main>
  );
}
