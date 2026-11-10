export type Role =
  | "STUDENT"
  | "MENTOR"
  | "PLACEMENT_COORDINATOR"
  | "COLLEGE_ADMIN"
  | "SUPER_ADMIN";

export type RecordStatus = "ACTIVE" | "INACTIVE";
export type UserStatus = "ACTIVE" | "SUSPENDED" | "GRADUATED" | "DEACTIVATED";

export interface HealthResponse {
  status: "ok";
  name: string;
  version: string;
  environment: "development" | "test" | "staging" | "production";
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
    request_id: string | null;
  };
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface LoginRequest {
  college_code: string;
  email: string;
  password: string;
}

export interface MeResponse {
  user_id: string;
  college_id: string;
  college_name: string;
  college_code: string;
  email: string;
  display_name: string;
  status: string;
  roles: Role[];
}

export interface AuthConfigResponse {
  oidc_enabled: boolean;
}

export interface OidcStartResponse {
  authorization_url: string;
}

export interface College {
  id: string;
  name: string;
  short_code: string;
  domain: string | null;
  status: string;
  timezone: string;
}

export interface CollegeCreate {
  name: string;
  short_code: string;
  domain?: string | null;
  timezone?: string;
}

export interface Department {
  id: string;
  code: string;
  name: string;
  status: string;
}

export interface DepartmentCreate {
  code: string;
  name: string;
}

export interface DepartmentUpdate {
  name?: string;
  status?: RecordStatus;
}

export interface Batch {
  id: string;
  department_id: string;
  name: string;
  start_year: number;
  end_year: number;
  status: string;
}

export interface BatchCreate {
  department_id: string;
  name: string;
  start_year: number;
  end_year: number;
}

export interface Mentor {
  id: string;
  user_id: string;
  email: string;
  display_name: string;
  employee_code: string;
  department_id: string | null;
  status: string;
}

export interface MentorCreate {
  email: string;
  display_name: string;
  employee_code: string;
  department_id?: string | null;
  temporary_password?: string | null;
}

export interface Assignment {
  id: string;
  mentor_id: string;
  batch_id: string;
  assigned_at: string;
}

export interface Student {
  id: string;
  user_id: string;
  register_number: string;
  display_name: string;
  email: string;
  department_id: string;
  department_name: string;
  batch_id: string;
  batch_name: string;
  admission_year: number | null;
  current_year: number | null;
  status: string;
}

export interface StudentUpdate {
  display_name?: string;
  current_year?: number;
}

export interface ImportRowError {
  row: number;
  message: string;
}

export interface ImportResult {
  created: number;
  skipped: number;
  failed: number;
  errors: ImportRowError[];
}

export interface AuditLog {
  id: string;
  actor_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: Record<string, unknown>;
  request_id: string | null;
  occurred_at: string;
}

export interface StudentListParams {
  page?: number;
  page_size?: number;
  department_id?: string;
  batch_id?: string;
  status?: string;
  search?: string;
}

export interface AuditListParams {
  page?: number;
  page_size?: number;
}
