// 전체 CT 분석 이력 조회 API
// GET /api/v1/history/

import apiClient from "./axios";
import type {
  AnalysisStatus,
} from "./analysis";

export type HistoryItem = {
  case_id: number;
  job_id: string;
  patient_id: string;
  patient_name: string;
  status: AnalysisStatus;
  progress: number;
  created_at: string;
};

export type HistoryResponse = {
  results: HistoryItem[];
};

export async function getAnalysisHistory(): Promise<HistoryResponse> {
  const response =
    await apiClient.get<HistoryResponse>(
      "/api/v1/history/",
    );

  return response.data;
}
