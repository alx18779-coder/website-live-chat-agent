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
  const headers = new Headers(init?.headers ?? {});
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  if (apiKey && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${apiKey}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: init?.credentials ?? 'omit',
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
