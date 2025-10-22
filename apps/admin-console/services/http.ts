export interface HttpErrorPayload {
  message: string;
  code?: string;
  error_detail?: unknown;
}

export class HttpError extends Error {
  status: number;
  payload?: HttpErrorPayload;
  requestId?: string;

  constructor(message: string, status: number, payload?: HttpErrorPayload, requestId?: string) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.payload = payload;
    this.requestId = requestId;
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    credentials: 'include',
  });

  const requestId = response.headers.get('x-request-id') ?? undefined;

  if (!response.ok) {
    let payload: HttpErrorPayload | undefined;
    try {
      payload = (await response.json()) as HttpErrorPayload;
    } catch (error) {
      // ignore parse errors
    }
    throw new HttpError(payload?.message ?? '请求失败', response.status, payload, requestId);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
