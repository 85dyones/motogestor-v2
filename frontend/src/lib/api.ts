export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

const API_URL = import.meta.env.VITE_API_URL || "";

type RequestOptions = {
  method?: string;
  token?: string | null;
  body?: unknown;
  headers?: Record<string, string>;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", token, body, headers = {} } = options;
  const resp = await fetch(`${API_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers
    },
    body: body ? JSON.stringify(body) : undefined
  });

  const contentType = resp.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await resp.json() : undefined;

  if (!resp.ok) {
    const message = payload?.error?.message || payload?.msg || `Erro ${resp.status}`;
    throw new ApiError(message, resp.status, payload?.error?.details ?? payload);
  }

  return (payload as T) ?? ({} as T);
}
