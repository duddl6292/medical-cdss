import apiClient from "./axios";
import type { AnalysisStatus } from "./analysis";

export type DashboardItem = {
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
};

export type DashboardResponse = {
  summary: {
    total: number;
    completed: number;
    processing: number;
    waiting: number;
    failed: number;
  };
  recent: DashboardItem[];
  generated_at: string | null;
};

export type NotificationResponse = {
  count: number;
  results: DashboardItem[];
};

export type SystemHealth = {
  status: "healthy" | "degraded";
  services: {
    django: string;
    database: string;
    inference: string;
  };
};

export async function getDashboard(): Promise<DashboardResponse> {
  return (await apiClient.get<DashboardResponse>("/api/v1/dashboard/")).data;
}

export async function getNotifications(): Promise<NotificationResponse> {
  return (
    await apiClient.get<NotificationResponse>("/api/v1/notifications/")
  ).data;
}

export async function getSystemHealth(): Promise<SystemHealth> {
  return (
    await apiClient.get<SystemHealth>("/api/v1/system/health/")
  ).data;
}
