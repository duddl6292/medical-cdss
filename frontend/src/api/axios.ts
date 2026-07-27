// Django API 공통 요청 설정
// API 기본 주소 예시: http://localhost:8000



import axios from "axios";

const apiClient = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ??
    "http://localhost:8000",

  timeout: 360000,
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",

  headers: {
    Accept: "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,

  (error) => {
    const message =
      error.response?.data?.message ??
      error.response?.data?.detail ??
      error.message ??
      "API 요청 중 오류가 발생했습니다.";

    return Promise.reject(
      new Error(message),
    );
  },
);

export default apiClient;
