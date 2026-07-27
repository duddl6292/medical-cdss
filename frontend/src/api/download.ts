import apiClient from "./axios";

export type ResultArtifact =
  | "original"
  | "mask"
  | "result"
  | "preview"
  | "probability"
  | "entropy"
  | "uncertainty";

export async function downloadResultFile(
  ctId: number,
  artifact: ResultArtifact = "mask",
): Promise<void> {
  const response =
    await apiClient.get<Blob>(
      `/api/v1/result/${ctId}/artifacts/${artifact}/`,
      {
        params: { download: 1 },
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
  link.download = getDownloadFilename(
    ctId,
    artifact,
    response.headers["content-disposition"],
  );

  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(
    downloadUrl,
  );
}

function getDownloadFilename(
  ctId: number,
  artifact: ResultArtifact,
  contentDisposition?: string,
): string {
  const encodedFilename = contentDisposition?.match(
    /filename\*=UTF-8''([^;]+)/i,
  )?.[1];
  const filename = contentDisposition?.match(
    /filename="?([^";]+)"?/i,
  )?.[1];

  if (encodedFilename) {
    return decodeURIComponent(encodedFilename);
  }

  return filename ?? `ct-${ctId}-${artifact}`;
}
