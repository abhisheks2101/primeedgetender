import { getApiBaseUrl } from "@/lib/utils";

export type TenderSourceType = "GOVERNMENT_PORTAL" | "API" | "PUBLIC_DATA" | "OTHER";
export type CollectionMethod = "HTTP" | "API" | "HTML" | "DOCUMENT" | "OTHER";
export type SourceHealthStatus = "HEALTHY" | "DEGRADED" | "FAILED" | "UNKNOWN";
export type CollectionJobStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "PARTIAL"
  | "FAILED"
  | "CANCELLED";

export interface SourceConfiguration {
  source_url?: string | null;
  search_url?: string | null;
  detail_url_pattern?: string | null;
  document_url_pattern?: string | null;
  request_timeout_seconds?: number;
  retry_count?: number;
  request_delay_seconds?: number;
  max_requests_per_collection?: number;
  pagination?: Record<string, unknown> | null;
}

export interface TenderSourceSummary {
  id: string;
  name: string;
  code: string;
  state?: string | null;
  authority?: string | null;
  source_type: TenderSourceType;
  collection_method: CollectionMethod;
  is_active: boolean;
  health_status: SourceHealthStatus;
  priority: number;
  last_success_at?: string | null;
  last_failure_at?: string | null;
  last_error?: string | null;
}

export interface TenderSource extends TenderSourceSummary {
  portal_url?: string | null;
  description?: string | null;
  configuration: SourceConfiguration;
  last_collection_started_at?: string | null;
  last_collection_completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectionJobSummary {
  id: string;
  tender_source_id: string;
  source_name?: string | null;
  source_code?: string | null;
  status: CollectionJobStatus;
  started_at?: string | null;
  completed_at?: string | null;
  records_discovered: number;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_skipped: number;
  records_failed: number;
  duration_seconds?: number | null;
  error_message?: string | null;
  created_at: string;
}

export interface TenderSourceInput {
  name: string;
  code: string;
  state?: string | null;
  authority?: string | null;
  portal_url?: string | null;
  source_type: TenderSourceType;
  collection_method: CollectionMethod;
  priority?: number;
  description?: string | null;
  configuration?: SourceConfiguration;
  is_active?: boolean;
}

async function apiFetch<T>(path: string, init?: RequestInit, cookieHeader?: string): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (cookieHeader) headers.cookie = cookieHeader;
  if (init?.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
    credentials: cookieHeader ? undefined : "include",
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function listTenderSources(cookieHeader?: string, activeOnly?: boolean) {
  const query = activeOnly === undefined ? "" : `?active_only=${activeOnly}`;
  return apiFetch<TenderSourceSummary[]>(`/api/tender-sources${query}`, undefined, cookieHeader);
}

export function getTenderSource(id: string, cookieHeader?: string) {
  return apiFetch<TenderSource>(`/api/tender-sources/${id}`, undefined, cookieHeader);
}

export function createTenderSource(payload: TenderSourceInput) {
  return apiFetch<TenderSource>("/api/tender-sources", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTenderSource(id: string, payload: Partial<TenderSourceInput>) {
  return apiFetch<TenderSource>(`/api/tender-sources/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateTenderSourceStatus(
  id: string,
  payload: { is_active: boolean; health_status?: SourceHealthStatus },
) {
  return apiFetch<TenderSource>(`/api/tender-sources/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function listSourceJobs(sourceId: string, cookieHeader?: string) {
  return apiFetch<CollectionJobSummary[]>(`/api/tender-sources/${sourceId}/jobs`, undefined, cookieHeader);
}

export function listCollectionJobs(cookieHeader?: string) {
  return apiFetch<CollectionJobSummary[]>("/api/tender-collection/jobs", undefined, cookieHeader);
}
