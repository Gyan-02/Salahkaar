import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi, it, expect } from "vitest";
import { Guidelines } from "../pages/Guidelines";

it("renders the honest no-match state without an inferred answer", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        result: null,
        status: "NO_OFFICIAL_SOURCE_MATCH",
      }),
    }),
  );
  render(<Guidelines />);
  fireEvent.change(screen.getByLabelText(/what would you like/i), {
    target: { value: "Which documents are required?" },
  });
  fireEvent.click(screen.getByRole("button", { name: /search sources/i }));
  await waitFor(() =>
    expect(
      screen.getByText(
        "No matching passage was found in the official sources currently loaded.",
      ),
    ).toBeInTheDocument(),
  );
  expect(screen.queryByText(/you may need/i)).not.toBeInTheDocument();
});
