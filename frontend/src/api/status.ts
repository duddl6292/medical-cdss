// CT 분석 상태 및 진행률 조회 API
// GET /api/v1/status/{case_id}/

import apiClient from "./axios";
import type {
  AnalysisStatus,
} from "./analysis";

export type StatusResponse = {
  case_id: number;
  job_id: number;
  status: AnalysisStatus;
  progress: number;
  elapsed_time: number;
  error_message: string | null;
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