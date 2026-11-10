import type {
  Assignment,
  AuditListParams,
  AuditLog,
  AuthConfigResponse,
  Batch,
  BatchCreate,
  College,
  CollegeCreate,
  Department,
  DepartmentCreate,
  DepartmentUpdate,
  HealthResponse,
  ImportResult,
  LoginRequest,
  MeResponse,
  Mentor,
  MentorCreate,
  OidcStartResponse,
  Page,
  Student,
  StudentListParams,
  StudentUpdate,
  UserStatus,
} from "../types/api";
import type { ApiErrorBody } from "../types/api";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;

  constructor(message: string, status: number, code: string, requestId: string | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      body = null;
    }

    throw new ApiError(
      body?.error.message ?? `Request failed with status ${response.status}`,
      response.status,
      body?.error.code ?? "http_error",
      body?.error.request_id ?? response.headers.get("X-Request-ID"),
    );
  }

  return (await response.json()) as T;
}

function toQuery(params: Record<string, string | number | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export const authApi = {
  config: () => request<AuthConfigResponse>("/auth/config"),
  login: (payload: LoginRequest) =>
    request<MeResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<MeResponse>("/auth/me"),
  oidcStart: (collegeCode: string) =>
    request<OidcStartResponse>(
      `/auth/oidc/start${toQuery({ college_code: collegeCode })}`,
    ),
};

export const studentsApi = {
  list: (params: StudentListParams = {}) =>
    request<Page<Student>>(`/students${toQuery({ ...params })}`),
  me: () => request<Student>("/students/me"),
  updateMe: (payload: StudentUpdate) =>
    request<Student>("/students/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};

export const adminApi = {
  listColleges: () => request<College[]>("/admin/colleges"),
  createCollege: (payload: CollegeCreate) =>
    request<College>("/admin/colleges", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listDepartments: () => request<Department[]>("/admin/departments"),
  createDepartment: (payload: DepartmentCreate) =>
    request<Department>("/admin/departments", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateDepartment: (departmentId: string, payload: DepartmentUpdate) =>
    request<Department>(`/admin/departments/${departmentId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listBatches: (departmentId?: string) =>
    request<Batch[]>(`/admin/batches${toQuery({ department_id: departmentId })}`),
  createBatch: (payload: BatchCreate) =>
    request<Batch>("/admin/batches", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listMentors: () => request<Mentor[]>("/admin/mentors"),
  createMentor: (payload: MentorCreate) =>
    request<Mentor>("/admin/mentors", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  assignMentor: (mentorId: string, batchId: string) =>
    request<Assignment>("/admin/mentors/assign", {
      method: "POST",
      body: JSON.stringify({ mentor_id: mentorId, batch_id: batchId }),
    }),
  importStudents: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ImportResult>("/admin/students/import", {
      method: "POST",
      body: form,
    });
  },
  updateUserStatus: (userId: string, status: UserStatus) =>
    request<void>(`/admin/users/${userId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  listAuditLogs: (params: AuditListParams = {}) =>
    request<Page<AuditLog>>(`/admin/audit-logs${toQuery({ ...params })}`),
};
