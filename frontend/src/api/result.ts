// CT 분석 결과 조회 API
// GET /api/v1/result/{case_id}/

import apiClient from "./axios";
import type {
  AnalysisStatus,
} from "./analysis";

export type ResultResponse = {
  case_id: number;
  subject_id: string;
  job_id: string;
  status: AnalysisStatus;
  progress: number;
  elapsed_time: number;

  original_nifti_url: string | null;
  mask_nifti_url: string | null;
  preview_image_url: string | null;
  result_json_uri: string | null;
  probability_uri: string | null;
  entropy_uri: string | null;
  uncertainty_uri: string | null;

  lesion_volume_ml: number | null;
  lesion_slice_count: number;
  lesion_slice_start: number | null;
  lesion_slice_end: number | null;
  max_lesion_slice: number | null;
  model_id: string;
  model_version: string | null;
  folds: number[];
  checkpoint: string;
  inference_time_seconds: number;
  gpu_peak_memory_mb: number | null;
  message: string;
  error_message: string | null;
  review_status: "pending" | "reviewed";
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_note: string;

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

export async function reviewAnalysisResult(
  caseId: number,
  reviewNote: string,
): Promise<{
  review_status: "reviewed";
  reviewed_by: string;
  reviewed_at: string;
  review_note: string;
}> {
  const response = await apiClient.post(
    `/api/v1/result/${caseId}/review/`,
    { note: reviewNote },
  );
  return response.data;
}
