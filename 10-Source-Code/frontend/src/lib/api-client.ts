import type { ResponseEnvelope } from "@/lib/types";

export class ApiError extends Error {
  code: string;
  status: number;
  details: unknown[];

  constructor(status: number, code: string, message: string, details: unknown[] = []) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("aims_access_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem("aims_access_token", token);
  else window.localStorage.removeItem("aims_access_token");
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  skipAuth?: boolean;
}

// Both the Core API and the AI Engine service validate the same JWT (they share
// JWT_SECRET_KEY — see ai-service/.env.example), so one token from login works against
// either backend. This factory lets each service get its own base URL while sharing
// every other concern (auth header, envelope unwrapping, 401 handling).
function createApiClient(baseUrl: string) {
  async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { method = "GET", body, query, skipAuth } = options;

    const url = new URL(`${baseUrl}${path}`);
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined) url.searchParams.set(key, String(value));
      });
    }

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    const token = getToken();
    if (token && !skipAuth) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(url.toString(), {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401) {
      setToken(null);
      if (typeof window !== "undefined") window.location.href = "/login";
      throw new ApiError(401, "UNAUTHENTICATED", "Session expired, please log in again");
    }

    const envelope = (await res.json()) as ResponseEnvelope<T>;

    if (!res.ok || !envelope.success) {
      const err = envelope.error;
      throw new ApiError(res.status, err?.code ?? "UNKNOWN_ERROR", err?.message ?? "Request failed", err?.details ?? []);
    }

    return envelope.data as T;
  }

  return {
    get: <T>(path: string, query?: RequestOptions["query"]) => request<T>(path, { method: "GET", query }),
    post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
    put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
    del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/v1";
const AI_API_BASE_URL = process.env.NEXT_PUBLIC_AI_API_BASE_URL ?? "http://localhost:8001/v1";

export const apiClient = createApiClient(API_BASE_URL);
export const aiApiClient = createApiClient(AI_API_BASE_URL);
