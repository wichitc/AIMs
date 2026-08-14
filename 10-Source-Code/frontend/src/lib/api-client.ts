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
  // Every list endpoint returns pagination info in envelope.meta, but historically nothing
  // in the app read it past this point — request<T>() returned only envelope.data, so every
  // page either had no real page count or faked one. unwrapEnvelope() keeps meta around;
  // request() still discards it (unchanged behavior for every existing caller), and
  // requestWithMeta() is the opt-in path for callers that want the real total.
  async function unwrapEnvelope<T>(res: Response): Promise<ResponseEnvelope<T>> {
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

    return envelope;
  }

  async function fetchEnvelope<T>(path: string, options: RequestOptions = {}): Promise<ResponseEnvelope<T>> {
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

    return unwrapEnvelope<T>(res);
  }

  async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const envelope = await fetchEnvelope<T>(path, options);
    return envelope.data as T;
  }

  // multipart/form-data (file uploads) — deliberately does NOT set Content-Type; the
  // browser must generate it itself (includes the multipart boundary), setting it manually
  // here would break the upload.
  async function postFormData<T>(path: string, formData: FormData): Promise<T> {
    const headers: Record<string, string> = {};
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`${baseUrl}${path}`, { method: "POST", headers, body: formData });
    const envelope = await unwrapEnvelope<T>(res);
    return envelope.data as T;
  }

  return {
    get: <T>(path: string, query?: RequestOptions["query"]) => request<T>(path, { method: "GET", query }),
    // Opt-in variant for list pages that want the real pagination total instead of guessing
    // from result length. Returns {data, meta} — meta is null for non-paginated endpoints.
    getWithMeta: <T>(path: string, query?: RequestOptions["query"]) =>
      fetchEnvelope<T>(path, { method: "GET", query }).then((e) => ({ data: e.data as T, meta: e.meta ?? null })),
    post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
    put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
    del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
    postFormData,
  };
}

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/v1";
const AI_API_BASE_URL = process.env.NEXT_PUBLIC_AI_API_BASE_URL ?? "http://localhost:8001/v1";

export const apiClient = createApiClient(API_BASE_URL);
export const aiApiClient = createApiClient(AI_API_BASE_URL);

// File download — the response is a raw binary stream, not a ResponseEnvelope, so it can't
// go through apiClient.get(). A plain <a href> wouldn't carry the Authorization header the
// endpoint requires, hence fetch + blob + a synthetic click.
export async function downloadFile(path: string, suggestedFileName: string): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    throw new ApiError(res.status, "DOWNLOAD_FAILED", "Failed to download file");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = suggestedFileName;
  link.click();
  URL.revokeObjectURL(url);
}
