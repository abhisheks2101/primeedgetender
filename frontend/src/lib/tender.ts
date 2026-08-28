import { getApiBaseUrl } from "@/lib/utils";

export type TenderStatus = "OPEN" | "CLOSED" | "CANCELLED" | "AWARDED" | "UNKNOWN";
export type IndianStateCode = "UTTAR_PRADESH" | "MADHYA_PRADESH" | "UNKNOWN";
export type NormalizationStatus = "NOT_PROCESSED" | "NORMALIZED" | "FAILED" | "NEEDS_REVIEW";
export type DuplicateMatchType = "EXACT_DUPLICATE" | "LIKELY_DUPLICATE" | "POSSIBLE_DUPLICATE" | "NOT_DUPLICATE";
export type DuplicateReviewStatus = "PENDING" | "CONFIRMED_DUPLICATE" | "NOT_DUPLICATE" | "IGNORED";

export interface TenderSummary {
  id: string;
  tender_source_id: string;
  source_tender_id: string;
  reference_number?: string | null;
  title?: string | null;
  organization?: string | null;
  location?: string | null;
  state?: string | null;
  state_code: IndianStateCode;
  status: TenderStatus;
  normalization_status: NormalizationStatus;
  submission_end?: string | null;
  estimated_value?: string | null;
}

export interface TenderDocument {
  id: string;
  document_name: string;
  document_url?: string | null;
  document_type?: string | null;
  source_reference?: string | null;
}

export interface Tender extends TenderSummary {
  work_description?: string | null;
  department?: string | null;
  tender_type?: string | null;
  tender_category?: string | null;
  district?: string | null;
  original_location_text?: string | null;
  emd_amount?: string | null;
  tender_fee?: string | null;
  publication_date?: string | null;
  document_sale_start?: string | null;
  document_sale_end?: string | null;
  submission_start?: string | null;
  opening_date?: string | null;
  source_status?: string | null;
  source_url?: string | null;
  source_last_updated?: string | null;
  normalization_version: number;
  validation_warnings?: string[] | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  normalized_at?: string | null;
  created_at: string;
  updated_at: string;
  documents: TenderDocument[];
}

export interface TenderDuplicateTenderSummary {
  id: string;
  tender_source_id: string;
  source_tender_id: string;
  reference_number?: string | null;
  title?: string | null;
  organization?: string | null;
  state_code: IndianStateCode;
  status: TenderStatus;
}

export interface TenderDuplicateCandidate {
  id: string;
  tender_id: string;
  candidate_tender_id: string;
  match_type: DuplicateMatchType;
  confidence: number;
  matched_fields?: string[] | null;
  review_status: DuplicateReviewStatus;
  created_at: string;
  reviewed_at?: string | null;
  tender?: TenderDuplicateTenderSummary | null;
  candidate_tender?: TenderDuplicateTenderSummary | null;
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

export function listTenders(cookieHeader?: string, limit = 50) {
  return apiFetch<TenderSummary[]>(`/api/tenders?limit=${limit}`, undefined, cookieHeader);
}

export function getTender(id: string, cookieHeader?: string) {
  return apiFetch<Tender>(`/api/tenders/${id}`, undefined, cookieHeader);
}

export function listTenderDuplicates(cookieHeader?: string, reviewStatus?: DuplicateReviewStatus) {
  const query = reviewStatus ? `?review_status=${reviewStatus}` : "";
  return apiFetch<TenderDuplicateCandidate[]>(`/api/tender-duplicates${query}`, undefined, cookieHeader);
}

export function reviewTenderDuplicate(id: string, reviewStatus: DuplicateReviewStatus) {
  return apiFetch<TenderDuplicateCandidate>(`/api/tender-duplicates/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ review_status: reviewStatus }),
  });
}
