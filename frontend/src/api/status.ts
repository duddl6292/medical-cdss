// CT 분석 상태 및 진행률 조회 API
// GET /api/v1/status/{case_id}/

import apiClient from "./axios";
import type {
  AnalysisStatus,
} from "./analysis";

export type StatusResponse = {
  case_id: number;
  subject_id: string;
  job_id: string;
  status: AnalysisStatus;
  progress: number;
  review_status: "pending" | "reviewed";
  elapsed_time: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export async function getAnalysisStatus(
  caseId: number,
): Promise<StatusResponse> {
  const response =
    await apiClient.get<StatusResponse>(
      `/api/v1/status/${caseId}/`,
    );

  return response.data;
}
