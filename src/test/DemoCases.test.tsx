import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, it, expect } from "vitest";
import { DemoCases } from "../pages/DemoCases";

it("runs demo cases through the backend route", async () => {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
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
      case_id: "pm-kisan-clean-readiness",
    }),
  });
  vi.stubGlobal("fetch", fetchMock);
  render(
    <MemoryRouter>
      <DemoCases />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getAllByRole("button", { name: /run this case/i })[1]);
  await waitFor(() => expect(fetchMock).toHaveBeenCalled());
  expect(fetchMock.mock.calls[0][0]).toContain(
    "/demo/run/pm-kisan-clean-readiness",
  );
});
