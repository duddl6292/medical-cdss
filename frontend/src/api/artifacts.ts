import apiClient from "./axios";

export async function getArtifactObjectUrl(url: string): Promise<string> {
  const response = await apiClient.get<Blob>(url, {
    responseType: "blob",
  });
  return URL.createObjectURL(response.data);
}
