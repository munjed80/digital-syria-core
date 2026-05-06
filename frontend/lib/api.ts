import type {
  ServiceItem,
  ServiceRequest,
  ServiceRequestDetail,
  TokenResponse,
  User,
} from './types';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export const TOKEN_STORAGE_KEY = 'dsc_access_token';
export const TOKEN_COOKIE_NAME = 'dsc_access_token';

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function storeToken(token: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    /* ignore quota errors */
  }
  // Mirror the token into a non-HttpOnly cookie so the Next.js middleware can
  // perform server-side redirects for protected routes. This is a pragmatic
  // trade-off for an MVP that uses a JWT bearer flow; a production hardening
  // step is to move to HttpOnly cookies issued by the backend.
  const maxAgeSeconds = 60 * 60 * 8; // 8 hours
  const secureFlag = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `${TOKEN_COOKIE_NAME}=${encodeURIComponent(
    token,
  )}; Path=/; Max-Age=${maxAgeSeconds}; SameSite=Lax${secureFlag}`;
}

export function clearToken(): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    /* ignore */
  }
  document.cookie = `${TOKEN_COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax`;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  token?: string | null;
  headers?: Record<string, string>;
  asForm?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token, headers = {}, asForm = false } = options;

  const finalHeaders: Record<string, string> = { Accept: 'application/json', ...headers };
  let payload: BodyInit | undefined;

  if (body !== undefined) {
    if (asForm && body instanceof URLSearchParams) {
      finalHeaders['Content-Type'] = 'application/x-www-form-urlencoded';
      payload = body;
    } else {
      finalHeaders['Content-Type'] = 'application/json';
      payload = JSON.stringify(body);
    }
  }

  const authToken = token === undefined ? getStoredToken() : token;
  if (authToken) {
    finalHeaders['Authorization'] = `Bearer ${authToken}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: payload,
    });
  } catch (err) {
    throw new ApiError(0, 'تعذّر الاتصال بالخادم. يرجى التحقق من الشبكة.', err);
  }

  const text = await response.text();
  const data = text ? safeJsonParse(text) : null;

  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail) && detail.length > 0
        ? formatValidationDetail(detail)
        : `حدث خطأ (${response.status})`;
    throw new ApiError(response.status, message, detail);
  }

  return data as T;
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function formatValidationDetail(detail: unknown[]): string {
  const first = detail[0] as { msg?: string } | undefined;
  return first?.msg ? first.msg : 'بيانات غير صالحة';
}

export const api = {
  async login(email: string, password: string): Promise<TokenResponse> {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    return request<TokenResponse>('/auth/token', {
      method: 'POST',
      body: form,
      asForm: true,
      token: null,
    });
  },

  async register(full_name: string, email: string, password: string): Promise<User> {
    return request<User>('/auth/register', {
      method: 'POST',
      body: { full_name, email, password },
      token: null,
    });
  },

  async me(token?: string): Promise<User> {
    return request<User>('/auth/me', { token });
  },

  async listServices(token?: string): Promise<ServiceItem[]> {
    return request<ServiceItem[]>('/services', { token });
  },

  async listRequests(token?: string): Promise<ServiceRequest[]> {
    return request<ServiceRequest[]>('/requests', { token });
  },

  async getRequest(id: number, token?: string): Promise<ServiceRequestDetail> {
    return request<ServiceRequestDetail>(`/requests/${id}`, { token });
  },

  async createRequest(
    payload: { service_id: number; title: string; description: string },
    token?: string,
  ): Promise<ServiceRequest> {
    return request<ServiceRequest>('/requests', {
      method: 'POST',
      body: payload,
      token,
    });
  },
};
