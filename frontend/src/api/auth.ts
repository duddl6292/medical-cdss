import apiClient from "./axios";

export type AuthUser = {
  id: number;
  username: string;
  name: string;
  email: string;
  role: "clinician" | "reviewer" | "admin";
  role_label: string;
  department: string;
  is_staff: boolean;
  is_superuser: boolean;
};

export async function fetchCsrf(): Promise<void> {
  await apiClient.get("/api/v1/auth/csrf/");
}

export async function loginUser(
  username: string,
  password: string,
): Promise<AuthUser> {
  await fetchCsrf();
  const response = await apiClient.post<AuthUser>(
    "/api/v1/auth/login/",
    { username, password },
  );
  return response.data;
}

export async function logoutUser(): Promise<void> {
  await apiClient.post("/api/v1/auth/logout/");
}

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await apiClient.get<AuthUser>("/api/v1/auth/me/");
  return response.data;
}
