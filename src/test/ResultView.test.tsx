import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import {
  ResultView,
  riskCopy,
  SourceReference,
} from "../components/ResultView";
import type { AnalysisResult, RiskReason } from "../types";

const base: AnalysisResult = {
  program: "pm-kisan",
  status: "PARTIAL_RULES_EVALUATED",
  eligible: null,
  readiness_score: 100,
  risk_level: "HIGH",
  risk_reason: "POLICY_INCOMPLETE",
  issues: [],
  blockers: [],
  actions: [],
  questions: [],
  explanations: [],
};
const show = (result: AnalysisResult) =>
  render(
    <MemoryRouter>
      <ResultView result={result} />
    </MemoryRouter>,
  );

describe("policy-safe result rendering", () => {
  it("renders PM-JAY pending without eligibility, readiness, risk or actions", () => {
    show({
      ...base,
      program: "ayushman-bharat-pm-jay",
      status: "OFFICIAL_RULES_PENDING",
      eligible: null,
      readiness_score: null,
      risk_level: "PENDING",
      actions: [
        {
          priority: 1,
          action_id: "bad",
          instruction: "Hidden action",
          reason: "Hidden",
        },
      ],
    });
    expect(
      screen.getByText("Criteria Pending Verification"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/^Eligible$/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Ineligible$/)).not.toBeInTheDocument();
    expect(screen.queryByText("Application readiness")).not.toBeInTheDocument();
    expect(screen.queryByText("Hidden action")).not.toBeInTheDocument();
    expect(
      screen.queryByText("Why this result needs attention"),
    ).not.toBeInTheDocument();
  });
  it("does not infer eligible from partial rules or a score of 100", () => {
    show(base);
    expect(
      screen.getByText("No failure found in the currently verified rules"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/^Eligible$/)).not.toBeInTheDocument();
  });
  it("shows verified-rule failure only for eligible false", () => {
    show({
      ...base,
      status: "INELIGIBLE",
      eligible: false,
      risk_reason: "ELIGIBILITY_FAILURE",
    });
    expect(
      screen.getByText("A verified eligibility rule was not satisfied", {
        selector: "h2",
      }),
    ).toBeInTheDocument();
  });
  it("keeps full readiness and policy risk visually distinct", () => {
    show(base);
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("POLICY INCOMPLETE")).toBeInTheDocument();
    expect(screen.getByText(riskCopy.POLICY_INCOMPLETE)).toBeInTheDocument();
  });
  it.each(Object.entries(riskCopy))(
    "maps %s to its approved explanation",
    (reason, copy) => {
      show({ ...base, risk_reason: reason as RiskReason });
      expect(screen.getByText(copy)).toBeInTheDocument();
    },
  );
  it("renders exact source text and source link", () => {
    render(
      <SourceReference
        reference={{
          text: "Exact official clause text.",
          source_url: "https://example.gov.in/rules",
          section_reference: "Section 4",
          score: 0.77,
        }}
      />,
    );
    expect(screen.getByText("Exact official clause text.")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /open official source/i }),
    ).toHaveAttribute("href", "https://example.gov.in/rules");
  });
  it("omits citations for a null official reference", () => {
    show({
      ...base,
      issues: [
        {
          code: "x",
          category: "DOCUMENT",
          severity: "MEDIUM",
          message: "Check this document.",
          evidence: [],
          official_reference: null,
        },
      ],
    });
    expect(
      screen.queryByText("Supported by official scheme text"),
    ).not.toBeInTheDocument();
  });
});
