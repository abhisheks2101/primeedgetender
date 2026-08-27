import { getApiBaseUrl } from "@/lib/utils";

export type UserRole = "ADMIN" | "USER";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AuthError {
  detail: string;
}

async function parseJson<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

function authHeaders(): HeadersInit {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
}

export async function loginRequest(email: string, password: string): Promise<{ ok: true; user: UserProfile } | { ok: false; error: string }> {
  const response = await fetch(`${getApiBaseUrl()}/api/auth/login`, {
    method: "POST",
    headers: authHeaders(),
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const payload = await parseJson<AuthError>(response);
    return { ok: false, error: payload.detail || "Login failed." };
  }

  const user = await parseJson<UserProfile>(response);
  return { ok: true, user };
}

export async function logoutRequest(): Promise<void> {
  await fetch(`${getApiBaseUrl()}/api/auth/logout`, {
    method: "POST",
    headers: authHeaders(),
    credentials: "include",
  });
}

export async function fetchCurrentUser(cookieHeader?: string): Promise<UserProfile | null> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  if (cookieHeader) {
    headers.cookie = cookieHeader;
  }

  const response = await fetch(`${getApiBaseUrl(Boolean(cookieHeader))}/api/auth/me`, {
    method: "GET",
    headers,
    credentials: cookieHeader ? undefined : "include",
    cache: "no-store",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Unable to fetch current user.");
  }

  return parseJson<UserProfile>(response);
}
