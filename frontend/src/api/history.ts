// 전체 CT 분석 이력 조회 API
// GET /api/v1/history/

import apiClient from "./axios";
import type {
  AnalysisStatus,
} from "./analysis";

export type HistoryItem = {
  case_id: number;
  job_id: string;
  subject_id: string;
  status: AnalysisStatus;
  progress: number;
  elapsed_time: number;
  review_status: "pending" | "reviewed";
  created_at: string;
  updated_at: string;
  error_message: string | null;
  result_available: boolean;
};

export type HistoryResponse = {
  count: number;
  results: HistoryItem[];
};

export async function getAnalysisHistory(params?: {
  q?: string;
  status?: string;
}): Promise<HistoryResponse> {
  const response =
    await apiClient.get<HistoryResponse>(
      "/api/v1/history/",
      { params },
    );

  return response.data;
}
