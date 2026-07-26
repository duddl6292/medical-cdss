// CT 분석 결과 조회 API
// GET /api/v1/result/{case_id}/

import apiClient from "./axios";
import type {
  AnalysisStatus,
} from "./analysis";

export type ResultResponse = {
  case_id: number;
  job_id: number;
  status: AnalysisStatus;
  progress: number;
  elapsed_time: number;

  original_nifti_url: string | null;
  mask_nifti_url: string | null;
  preview_image_url: string | null;

  lesion_volume_ml: number | null;
  confidence: number | null;
  model_version: string | null;
  error_message: string | null;

  created_at: string;
  updated_at: string;
};

export async function getAnalysisResult(
  caseId: number,
): Promise<ResultResponse> {
  const response =
    await apiClient.get<ResultResponse>(
      `/api/v1/result/${caseId}/`,
    );

  return response.data;
}