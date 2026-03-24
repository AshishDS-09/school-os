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

interface ParentIdentity {
  user_id?: number;
  email?: string;
}

type StudentRecord = Record<string, unknown>;

export interface ParentStudent {
  id: number;
  first_name: string;
  last_name: string;
  roll_number: string;
}

function parseParentStudent(record: StudentRecord | undefined): ParentStudent | null {
  if (!record) return null;

  const id = getNumberField(record, ["id"]);
  const firstName = getStringField(record, ["first_name"]);
  const lastName = getStringField(record, ["last_name"]);
  const rollNumber = getStringField(record, ["roll_number"]);

  if (
    id === null ||
    firstName === null ||
    lastName === null ||
    rollNumber === null
  ) {
    return null;
  }

  return {
    id,
    first_name: firstName,
    last_name: lastName,
    roll_number: rollNumber,
  };
}

function normalizeStudentList(payload: unknown): StudentRecord[] {
  if (Array.isArray(payload)) return payload.filter(Boolean) as StudentRecord[];
  if (!payload || typeof payload !== "object") return [];

  const candidateKeys = ["items", "results", "data"];
  for (const key of candidateKeys) {
    const value = (payload as Record<string, unknown>)[key];
    if (Array.isArray(value)) return value.filter(Boolean) as StudentRecord[];
  }

  return [];
}

function getNumberField(record: StudentRecord, keys: string[]): number | null {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() !== "" && !Number.isNaN(Number(value))) {
      return Number(value);
    }
  }

  return null;
}

function getStringField(record: StudentRecord, keys: string[]): string | null {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim() !== "") {
      return value.trim().toLowerCase();
    }
  }

  return null;
}

function matchStudentToParent(student: StudentRecord, parent: ParentIdentity): boolean {
  const parentUserId = parent.user_id;
  const parentEmail = parent.email?.trim().toLowerCase();

  if (parentUserId !== undefined) {
    const linkedParentId = getNumberField(student, [
      "parent_id",
      "parent_user_id",
      "guardian_id",
      "guardian_user_id",
      "user_id",
    ]);
    if (linkedParentId === parentUserId) return true;
  }

  if (parentEmail) {
    const linkedEmail = getStringField(student, [
      "parent_email",
      "guardian_email",
      "mother_email",
      "father_email",
      "email",
    ]);
    if (linkedEmail === parentEmail) return true;
  }

  return false;
}

export const parentApi = {
  // Get the child linked to this parent account
  getMyChild: (parent?: ParentIdentity) =>
    api.get("/api/students").then((r) => {
      const students = normalizeStudentList(r.data);

      if (students.length <= 1) {
        return parseParentStudent(students[0]);
      }

      if (!parent) {
        return null;
      }

      const match = students.find((student) => matchStudentToParent(student, parent));
      return parseParentStudent(match);
    }),
  getAttendance: (studentId: number, fromDate: string) =>
    api.get("/api/attendance", {
      params: { student_id: studentId, from_date: fromDate },
    }),
  getMarks: (studentId: number) =>
    api.get("/api/marks", { params: { student_id: studentId } }),
  getFees: (studentId: number) =>
    api.get("/api/fees",  { params: { student_id: studentId } }),
  getNotifications: (recipientId: number) =>
    api.get("/api/notifications", { params: { recipient_id: recipientId } }),
};
// Add to frontend/lib/api.ts

export const financeApi = {
  allFees:     (params?: { status?: string }) =>
    api.get("/api/fees", { params }),
  updateFee:   (id: number, data: unknown) =>
    api.patch(`/api/fees/${id}`, data),
};
// Add to frontend/lib/api.ts

export const leadsApi = {
  list:   (params?: { status?: string }) =>
    api.get("/api/leads", { params }),
  create: (data: unknown) => api.post("/api/leads", data),
  update: (id: number, data: unknown) =>
    api.patch(`/api/leads/${id}`, data),
};
