import type {
  AnalysisRequest,
  AnalysisResult,
  DemoCaseResponse,
  ExtractUploadResponse,
  GuidelineResponse,
  ProgramId,
  UploadResponse,
} from "./types";

const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
    /\/$/,
    "",
  ) ?? "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers:
        options.body instanceof FormData
          ? options.headers
          : { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    throw new ApiError(
      "Salahkaar could not reach the local analysis service. Please check that it is running and try again.",
    );
  }
  if (!response.ok) {
    let detail = `The service returned an error (${response.status}).`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      /* keep safe fallback */
    }
    throw new ApiError(detail, response.status);
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(
      "The service returned a response Salahkaar could not read.",
    );
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseAnalysis(value: unknown): AnalysisResult {
  if (
    !isRecord(value) ||
    typeof value.program !== "string" ||
    typeof value.status !== "string" ||
    !(typeof value.eligible === "boolean" || value.eligible === null) ||
    !(
      typeof value.readiness_score === "number" ||
      value.readiness_score === null
    ) ||
    typeof value.risk_level !== "string" ||
    !Array.isArray(value.issues) ||
    !Array.isArray(value.blockers) ||
    !Array.isArray(value.actions) ||
    !Array.isArray(value.questions) ||
    !Array.isArray(value.explanations)
  ) {
    throw new ApiError(
      "The analysis service returned an incomplete response. Please try again.",
    );
  }
  return value as unknown as AnalysisResult;
}

function parseGuidelines(value: unknown): GuidelineResponse {
  if (
    !isRecord(value) ||
    !["MATCH", "NO_OFFICIAL_SOURCE_MATCH"].includes(String(value.status)) ||
    !(Array.isArray(value.result) || value.result === null)
  ) {
    throw new ApiError(
      "The guideline service returned an incomplete response. Please try again.",
    );
  }
  return value as unknown as GuidelineResponse;
}

export const api = {
  uploadDocument: async (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<UploadResponse>("/documents/upload", {
      method: "POST",
      body,
    });
  },
  extractDocument: async (uploadToken: string, documentType: string) =>
    request<ExtractUploadResponse>("/documents/extract", {
      method: "POST",
      body: JSON.stringify({
        upload_token: uploadToken,
        document_type: documentType,
        consent_to_external_processing: true,
      }),
    }),
  runAnalysis: async (body: AnalysisRequest) =>
    parseAnalysis(
      await request<unknown>("/analysis/run", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    ),
  runDemo: async (caseId: string) => {
    const value = await request<unknown>(
      `/demo/run/${encodeURIComponent(caseId)}`,
      {
        method: "POST",
      },
    );
    const result = parseAnalysis(value);
    if (!isRecord(value) || typeof value.case_id !== "string") {
      throw new ApiError(
        "The demo service returned an incomplete response. Please try again.",
      );
    }
    return { ...result, case_id: value.case_id } as DemoCaseResponse;
  },
  lookupGuidelines: async (program: ProgramId, query: string) =>
    parseGuidelines(
      await request<unknown>("/guidelines/lookup", {
        method: "POST",
        body: JSON.stringify({ program, query, top_n: 3 }),
      }),
    ),
};
