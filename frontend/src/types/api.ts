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
