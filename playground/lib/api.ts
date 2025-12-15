import axios from "axios";

export type SensitivityLevel = "low" | "medium" | "high";

export type ChangeType = "FACTUAL" | "TONE" | "CONTENT" | "FORMATTING";
export type ChangeSeverity = "info" | "warning" | "critical";
export type SemanticChangeLevel = "NONE" | "MINOR" | "MODERATE" | "MAJOR" | "CRITICAL";

export interface TextSpan {
  text: string;
  start: number;
  end: number;
  context_before?: string;
  context_after?: string;
}

export interface SemanticChange {
  id: string;
  type: ChangeType;
  severity: ChangeSeverity;
  description: string;
  original_span: TextSpan;
  generated_span: TextSpan;
  reasoning: string;
}

export interface DiffSummary {
  is_safe: boolean;
  risk_score: number;
  semantic_change_level: SemanticChangeLevel;
}

export interface DiffResponse {
  summary: DiffSummary;
  changes: SemanticChange[];
}

export interface CompareRequest {
  original_text: string;
  generated_text: string;
  sensitivity?: SensitivityLevel;
  premium_mode?: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function compareTexts(request: CompareRequest): Promise<DiffResponse> {
  const response = await axios.post<DiffResponse>(
    `${API_BASE_URL}/v1/compare`,
    {
      original_text: request.original_text,
      generated_text: request.generated_text,
      sensitivity: request.sensitivity || "medium",
      premium_mode: request.premium_mode || false,
    },
    {
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 60000, // 60 seconds for safety
    }
  );

  return response.data;
}
