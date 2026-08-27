export type HealthStatus = "healthy" | "degraded" | "unhealthy";
export type ComponentStatus = "connected" | "disconnected" | "unknown";

export interface DatabaseHealth {
  status: "connected" | "disconnected";
  latency_ms?: number | null;
  error?: string | null;
}

export interface HealthResponse {
  status: HealthStatus;
  application: string;
  version: string;
  environment: string;
  database: DatabaseHealth;
}

export interface SystemStatusView {
  backend: ComponentStatus;
  database: ComponentStatus;
  overall: HealthStatus | "unknown";
  version?: string;
  environment?: string;
  databaseLatencyMs?: number | null;
  error?: string;
}

import { getApiBaseUrl } from "@/lib/utils";

export async function fetchHealthStatus(cookieHeader?: string): Promise<SystemStatusView> {
  const apiUrl = getApiBaseUrl(true);
  const headers: Record<string, string> = { Accept: "application/json" };
  if (cookieHeader) {
    headers.cookie = cookieHeader;
  }

  try {
    const response = await fetch(`${apiUrl}/api/health`, {
      cache: "no-store",
      headers,
    });

    if (!response.ok) {
      return {
        backend: "disconnected",
        database: "unknown",
        overall: "unhealthy",
        error: `Backend returned HTTP ${response.status}`,
      };
    }

    const data = (await response.json()) as HealthResponse;

    return {
      backend: "connected",
      database: data.database.status,
      overall: data.status,
      version: data.version,
      environment: data.environment,
      databaseLatencyMs: data.database.latency_ms,
      error: data.database.error ?? undefined,
    };
  } catch (error) {
    return {
      backend: "disconnected",
      database: "unknown",
      overall: "unknown",
      error: error instanceof Error ? error.message : "Unable to reach backend",
    };
  }
}

export function formatStatusLabel(status: ComponentStatus | HealthStatus | "unknown" | string): string {
  return status.replace("_", " ");
}
