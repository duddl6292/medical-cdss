// 분석 결과 파일 다운로드 API
// GET /api/v1/download/{case_id}/

import apiClient from "./axios";

export async function downloadResultFile(
  ctId: number,
): Promise<void> {
  const response =
    await apiClient.get<Blob>(
      `/api/v1/download/${ctId}/`,
      {
        responseType: "blob",
      },
    );

  const downloadUrl =
    window.URL.createObjectURL(
      response.data,
    );

  const link =
    document.createElement("a");

  link.href = downloadUrl;
  link.download =
    `ct-analysis-${ctId}.zip`;

  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(
    downloadUrl,
  );
}
