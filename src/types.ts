export type ProgramId = "pm-kisan" | "nmmss" | "ayushman-bharat-pm-jay";
export type AnalysisStatus =
  | "ELIGIBLE"
  | "INELIGIBLE"
  | "INFORMATION_REQUIRED"
  | "PARTIAL_RULES_EVALUATED"
  | "OFFICIAL_RULES_PENDING";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "PENDING";
export type RiskReason =
  | "POLICY_INCOMPLETE"
  | "DOCUMENT_BLOCKERS"
  | "ELIGIBILITY_FAILURE"
  | "MULTIPLE_FACTORS";

export interface OfficialReference {
  text: string;
  source_url: string;
  section_reference: string;
  score: number;
}
export interface AnalysisIssue {
  code: string;
  category: string;
  severity: RiskLevel;
  message: string;
  evidence: Record<string, unknown>[];
  official_reference: OfficialReference | null;
}
export interface PlannedAction {
  priority: number;
  action_id: string;
  instruction: string;
  reason: string;
}
export interface FollowUpQuestion {
  field: string;
  question: string;
  required_for_program: string | null;
}
export interface AnalysisResult {
  program: string;
  status: AnalysisStatus;
  eligible: boolean | null;
  readiness_score: number | null;
  risk_level: RiskLevel;
  risk_reason: RiskReason | null;
  issues: AnalysisIssue[];
  blockers: AnalysisIssue[];
  actions: PlannedAction[];
  questions: FollowUpQuestion[];
  explanations: string[];
}
export interface DemoCaseResponse extends AnalysisResult {
  case_id: string;
}
export interface AnalysisDocument {
  document_type: string;
  filename: string;
  fields: Record<string, unknown>;
}
export interface AnalysisRequest {
  program_id: ProgramId;
  documents: AnalysisDocument[];
  answers: Record<string, unknown>;
  document_quality: string[];
}
export interface RetrievedChunk {
  id: string;
  text: string;
  score: number;
  program: ProgramId;
  source_url: string;
  section_reference: string;
  retrieval_date: string;
  source_status: string;
}
export interface GuidelineResponse {
  result: RetrievedChunk[] | null;
  status: "MATCH" | "NO_OFFICIAL_SOURCE_MATCH";
}

export interface UploadResponse {
  upload_token: string;
  filename: string;
  content_type: string;
}

export interface ExtractionResult {
  document_type: string;
  fields: Record<string, unknown>;
  extractor: string;
  status: "SUCCEEDED" | "FAILED";
  fallback_used: boolean;
  failure_reason: string | null;
}

export interface ExtractUploadResponse {
  extraction: ExtractionResult;
  document: Record<string, unknown>;
}
