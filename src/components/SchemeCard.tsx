import { ArrowUpRight, HeartPulse, Landmark, Sprout } from "lucide-react";
import { Link } from "react-router-dom";
import type { SchemeConfig } from "../config";

export function SchemeCard({ scheme }: { scheme: SchemeConfig }) {
  const Icon =
    scheme.id === "pm-kisan"
      ? Sprout
      : scheme.id === "nmmss"
        ? Landmark
        : HeartPulse;
  return (
    <article className="scheme-card">
      <div className="scheme-icon">
        <Icon />
      </div>
      {scheme.pending && (
        <span className="pending-badge">Criteria verification pending</span>
      )}
      <p className="eyebrow">{scheme.eyebrow}</p>
      <h3>{scheme.name}</h3>
      <p>{scheme.description}</p>
      <Link to={`/check?scheme=${scheme.id}`}>
        Check readiness <ArrowUpRight size={18} />
      </Link>
    </article>
  );
}
