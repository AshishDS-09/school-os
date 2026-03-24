// frontend/lib/api.ts

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Single axios instance used by the whole app
export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// ── Request interceptor ───────────────────────────────────────────
// Automatically attach JWT token to every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Read token from localStorage
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor ──────────────────────────────────────────
// Handle 401 globally — redirect to login when token expires
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear stored token and redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── Typed API functions ───────────────────────────────────────────
// One function per API endpoint — keeps components clean

export const authApi = {
  login: (email: string, password: string) => {
    const formData = new URLSearchParams({
      username: email,
      password,
    });

    return api.post("/api/auth/login", formData.toString(), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  me: () => api.get("/api/auth/me"),
};

export const studentsApi = {
  list:   (params?: { class_id?: number; is_active?: boolean }) =>
    api.get("/api/students", { params }),
  get:    (id: number) => api.get(`/api/students/${id}`),
  create: (data: unknown) => api.post("/api/students", data),
  update: (id: number, data: unknown) => api.put(`/api/students/${id}`, data),
};

export const attendanceApi = {
  mark: (data: unknown) => api.post("/api/attendance", data),
  list: (params?: {
    student_id?: number;
    class_id?: number;
    from_date?: string;
    to_date?: string;
  }) => api.get("/api/attendance", { params }),
};

export const marksApi = {
  enter: (data: unknown) => api.post("/api/marks", data),
  list:  (params?: { student_id?: number; subject?: string }) =>
    api.get("/api/marks", { params }),
};

export const feesApi = {
  list:   (params?: { student_id?: number; status?: string }) =>
    api.get("/api/fees", { params }),
  create: (data: unknown) => api.post("/api/fees", data),
  update: (id: number, data: unknown) => api.patch(`/api/fees/${id}`, data),
};

export const agentLogsApi = {
  list: (params?: { agent_name?: string; limit?: number }) =>
    api.get("/api/agent-logs", { params }),
};

export const notificationsApi = {
  list: (params?: { recipient_id?: number }) =>
    api.get("/api/notifications", { params }),
};
