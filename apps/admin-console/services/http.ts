import { createLogger } from '@/services/logger';

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

const httpLogger = createLogger('http');

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  if (apiKey && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${apiKey}`);
  }

  const method = (init?.method ?? 'GET').toUpperCase();
  const startedAt = typeof performance !== 'undefined' ? performance.now() : Date.now();

  httpLogger.debug('开始发起请求', {
    method,
    path,
  });

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
      credentials: init?.credentials ?? 'omit',
    });
  } catch (error) {
    httpLogger.error('请求发送失败', {
      method,
      path,
      error,
    });
    throw error;
  }

  const completedAt = typeof performance !== 'undefined' ? performance.now() : Date.now();
  const durationMs = Math.round(completedAt - startedAt);

  const requestId = response.headers.get('x-request-id') ?? undefined;

  if (!response.ok) {
    let payload: HttpErrorPayload | undefined;
    try {
      payload = (await response.json()) as HttpErrorPayload;
    } catch (error) {
      // ignore parse errors
    }
    httpLogger.error('请求返回非成功状态', {
      method,
      path,
      status: response.status,
      requestId,
      durationMs,
      message: payload?.message ?? response.statusText,
    });
    throw new HttpError(payload?.message ?? '请求失败', response.status, payload, requestId);
  }

  if (response.status === 204) {
    httpLogger.debug('请求成功返回空内容', {
      method,
      path,
      status: response.status,
      requestId,
      durationMs,
    });
    return undefined as T;
  }

  const result = (await response.json()) as T;

  httpLogger.debug('请求成功完成', {
    method,
    path,
    status: response.status,
    requestId,
    durationMs,
  });

  return result;
}
