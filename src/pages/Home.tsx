import {
  ArrowRight,
  BookOpenCheck,
  Check,
  LockKeyhole,
  MapPin,
} from "lucide-react";
import { Link } from "react-router-dom";
import { schemes } from "../config";
import { SchemeCard } from "../components/SchemeCard";

export function Home() {
  return (
    <main>
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-copy">
            <span className="jurisdiction">
              <MapPin size={16} /> Bihar local demo
            </span>
            <h1>
              Get your benefits application <em>ready.</em>
            </h1>
            <p>
              Understand what your documents and information say before you
              apply. Salahkaar gives clear, grounded guidance without pretending
              to make an official decision.
            </p>
            <div className="hero-actions">
              <Link className="button button-primary" to="/check">
                Check my readiness <ArrowRight />
              </Link>
              <Link className="text-link" to="/demos">
                Explore demo cases
              </Link>
            </div>
            <p className="privacy-note">
              <LockKeyhole size={16} /> Single-user local demo. No account or
              registration.
            </p>
          </div>
          <div className="hero-panel">
            <div className="hero-panel-top">
              <span>How Salahkaar helps</span>
              <BookOpenCheck />
            </div>
            <ol>
              <li>
                <span>1</span>
                <div>
                  <strong>Choose a scheme</strong>
                  <p>Pick one of three supported benefit programmes.</p>
                </div>
              </li>
              <li>
                <span>2</span>
                <div>
                  <strong>Review your information</strong>
                  <p>Enter local mock details from your documents.</p>
                </div>
              </li>
              <li>
                <span>3</span>
                <div>
                  <strong>Get honest next steps</strong>
                  <p>See readiness, blockers, and grounded references.</p>
                </div>
              </li>
            </ol>
            <div className="not-approval">
              <Check />
              <p>
                <strong>Readiness, not approval.</strong>
                <br />
                Only the responsible authority can decide an application.
              </p>
            </div>
          </div>
        </div>
      </section>
      <section className="schemes-section page-shell">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Three supported schemes</span>
            <h2>Where would you like to begin?</h2>
          </div>
          <p>
            Each check uses only currently verified rules. Unknowns stay clearly
            marked.
          </p>
        </div>
        <div className="scheme-grid">
          {schemes.map((scheme) => (
            <SchemeCard key={scheme.id} scheme={scheme} />
          ))}
        </div>
      </section>
      <section className="principles">
        <div className="page-shell">
          <span className="eyebrow">Designed for clarity</span>
          <h2>Calm guidance. No false promises.</h2>
          <div className="principle-grid">
            <div>
              <strong>01</strong>
              <h3>Unknown stays unknown</h3>
              <p>
                We never turn incomplete policy coverage into an eligibility
                decision.
              </p>
            </div>
            <div>
              <strong>02</strong>
              <h3>Sources stay visible</h3>
              <p>
                Official passages are shown exactly as retrieved, with their
                source.
              </p>
            </div>
            <div>
              <strong>03</strong>
              <h3>Your next step is clear</h3>
              <p>
                Document issues and actions are separated from policy
                eligibility.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
