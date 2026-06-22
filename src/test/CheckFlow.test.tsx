import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { schemeById } from "../config";
import { buildRequest, CheckFlow } from "../pages/CheckFlow";

describe("readiness check flow", () => {
  it("blocks review when scheme questions are unanswered", () => {
    render(
      <MemoryRouter initialEntries={["/check?scheme=pm-kisan"]}>
        <CheckFlow />
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText(/name on identity record/i), {
      target: { value: "Ravi Kumar" },
    });
    const reviewButton = screen.getByRole("button", {
      name: /review information/i,
    });
    fireEvent.submit(reviewButton.closest("form")!);
    expect(
      screen.getByText(/7 answers are still missing/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/review before analysis/i),
    ).not.toBeInTheDocument();
  });

  it("preserves entered information when the backend is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(
      <MemoryRouter initialEntries={["/check?scheme=ayushman-bharat-pm-jay"]}>
        <CheckFlow />
      </MemoryRouter>,
    );

    const familyInput = screen.getByLabelText(/family member names/i);
    fireEvent.change(familyInput, { target: { value: "Meera, Arun" } });
    fireEvent.click(
      screen.getByRole("button", { name: /review information/i }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /run readiness analysis/i }),
    );

    await waitFor(() =>
      expect(
        screen.getByText(/could not reach the local analysis service/i),
      ).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole("button", { name: /edit information/i }));
    expect(screen.getByLabelText(/family member names/i)).toHaveValue(
      "Meera, Arun",
    );
  });

  it("keeps ISO date values unchanged in the API request", () => {
    const scheme = schemeById["pm-kisan"];
    const documents = Object.fromEntries(
      scheme.documents.map((document) => [
        document.type,
        Object.fromEntries(document.fields.map((field) => [field.key, ""])),
      ]),
    );
    documents.land_record.land_ownership_date = "2018-10-01";

    const request = buildRequest(scheme, {}, documents);
    expect(request.documents[0].fields.land_ownership_date).toBe("2018-10-01");
  });
});
