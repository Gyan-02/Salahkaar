import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../api";

describe("API response validation", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("rejects an incomplete analysis response instead of inventing defaults", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "PARTIAL_RULES_EVALUATED" }),
      }),
    );

    await expect(
      api.runAnalysis({
        program_id: "pm-kisan",
        documents: [],
        answers: {},
        document_quality: [],
      }),
    ).rejects.toThrow(
      "The analysis service returned an incomplete response. Please try again.",
    );
  });
});
