// CT NIfTI 파일 업로드 및 분석 요청 API
// POST /api/v1/cases/

import apiClient from "./axios";

export type AnalysisStatus =
  | "waiting"
  | "processing"
  | "completed"
  | "failed";

export type CaseCreateResponse = {
  case_id: number;
  job_id: number;
  status: AnalysisStatus;
  progress: number;
  created_at: string;
};

export async function requestAnalysis(
  ctFile: File,
): Promise<CaseCreateResponse> {
  const formData = new FormData();

  formData.append("ct_file", ctFile);

  const response =
    await apiClient.post<CaseCreateResponse>(
      "/api/v1/cases/",
      formData,
    );

  return response.data;
}