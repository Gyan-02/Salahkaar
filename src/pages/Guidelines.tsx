import {
  BookOpen,
  ExternalLink,
  LoaderCircle,
  Search,
  SearchX,
} from "lucide-react";
import { FormEvent, useState } from "react";
import { api, ApiError } from "../api";
import { schemes } from "../config";
import type { GuidelineResponse, ProgramId } from "../types";

const lookupExamples: Record<ProgramId, string> = {
  "pm-kisan": "income tax exclusion",
  nmmss: "parental income limit",
  "ayushman-bharat-pm-jay": "rural deprivation criteria",
};

export function Guidelines() {
  const [program, setProgram] = useState<ProgramId>("pm-kisan");
  const [query, setQuery] = useState("");
  const [data, setData] = useState<GuidelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lookup = async () => {
    if (query.trim().length < 3) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      setData(await api.lookupGuidelines(program, query.trim()));
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "The lookup could not be completed.",
      );
    } finally {
      setLoading(false);
    }
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    void lookup();
  };
  return (
    <main className="page-shell interior-page guideline-page">
      <div className="page-intro">
        <span className="eyebrow">
          <BookOpen size={15} /> Grounded retrieval
        </span>
        <h1>Official guideline lookup</h1>
        <p>
          Find exact passages from official scheme sources currently loaded in
          Salahkaar. This lookup does not generate or infer policy advice.
        </p>
      </div>
      <form className="lookup-form" onSubmit={submit}>
        <div className="lookup-fields">
          <label>
            Scheme
            <select
              value={program}
              onChange={(e) => {
                setProgram(e.target.value as ProgramId);
                setData(null);
              }}
            >
              {schemes.map((scheme) => (
                <option value={scheme.id} key={scheme.id}>
                  {scheme.shortName}
                </option>
              ))}
            </select>
          </label>
          <label className="query-field">
            What would you like to look up?
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              minLength={3}
              maxLength={500}
              placeholder={`For example: ${lookupExamples[program]}`}
            />
          </label>
          <button
            type="submit"
            className="button button-primary"
            disabled={loading || query.trim().length < 3}
          >
            {loading ? (
              <>
                <LoaderCircle className="spin" /> Searching…
              </>
            ) : (
              <>
                <Search /> Search sources
              </>
            )}
          </button>
        </div>
        <p>
          Exact passages are returned in relevance order. Nothing is merged or
          summarised.
        </p>
      </form>
      {error && (
        <div className="error-banner" role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => void lookup()}>
            Retry
          </button>
        </div>
      )}
      {data?.status === "NO_OFFICIAL_SOURCE_MATCH" && (
        <section className="no-match">
          <SearchX />
          <h2>No official source match</h2>
          <p>
            No matching passage was found in the official sources currently
            loaded.
          </p>
        </section>
      )}
      {data?.status === "MATCH" && data.result && (
        <section className="matches" aria-live="polite">
          <div className="matches-heading">
            <div>
              <span className="eyebrow">Official source passages</span>
              <h2>
                {data.result.length}{" "}
                {data.result.length === 1 ? "match" : "matches"} found
              </h2>
            </div>
            <span>Highest relevance first</span>
          </div>
          {data.result.map((chunk, index) => (
            <article className="chunk-card" key={chunk.id}>
              <div className="chunk-top">
                <span>Passage {index + 1}</span>
                <span>{chunk.program}</span>
              </div>
              <blockquote>{chunk.text}</blockquote>
              <dl>
                <div>
                  <dt>Section</dt>
                  <dd>{chunk.section_reference}</dd>
                </div>
                <div>
                  <dt>Retrieved</dt>
                  <dd>{chunk.retrieval_date}</dd>
                </div>
                <div>
                  <dt>Source status</dt>
                  <dd>{chunk.source_status}</dd>
                </div>
                <div>
                  <dt>Chunk ID</dt>
                  <dd>{chunk.id}</dd>
                </div>
              </dl>
              <div className="chunk-footer">
                <a href={chunk.source_url} target="_blank" rel="noreferrer">
                  Open official source <ExternalLink size={15} />
                </a>
                <details>
                  <summary>Technical score</summary>
                  <span>{chunk.score.toFixed(3)}</span>
                </details>
              </div>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
