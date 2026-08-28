import { getApiBaseUrl } from "@/lib/utils";

export type TenderDocumentDownloadStatus =
  | "DISCOVERED"
  | "DOWNLOAD_QUEUED"
  | "DOWNLOADING"
  | "DOWNLOADED"
  | "DOWNLOAD_FAILED"
  | "ACCESS_RESTRICTED";

export type TenderDocumentProcessingStatus = "PENDING" | "VALIDATED" | "INVALID" | "PROCESSING_FAILED" | "UNSUPPORTED";
export type TenderDocumentExtractionStatus =
  | "NOT_EXTRACTED"
  | "TEXT_EXTRACTED"
  | "OCR_REQUIRED"
  | "OCR_COMPLETED"
  | "EXTRACTION_FAILED";
export type TenderDocumentExtractionMethod = "NONE" | "DIRECT_EXTRACTION" | "OCR";

export interface TenderDocumentPage {
  id: string;
  page_number: number;
  text: string;
  extraction_method: TenderDocumentExtractionMethod;
  character_count: number;
}

export interface TenderDocumentSummary {
  id: string;
  tender_id: string;
  source_document_id: string;
  document_name: string;
  document_url?: string | null;
  classification: string;
  download_status: TenderDocumentDownloadStatus;
  processing_status: TenderDocumentProcessingStatus;
  extraction_status: TenderDocumentExtractionStatus;
  extraction_method: TenderDocumentExtractionMethod;
  mime_type?: string | null;
  file_extension?: string | null;
  file_size?: number | null;
  checksum?: string | null;
  page_count?: number | null;
  character_count?: number | null;
  error_code?: string | null;
  error_message?: string | null;
  downloaded_at?: string | null;
  processed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TenderDocument extends TenderDocumentSummary {
  document_type?: string | null;
  local_storage_path?: string | null;
  text_storage_path?: string | null;
  previous_checksum?: string | null;
  first_seen_at?: string | null;
  pages: TenderDocumentPage[];
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

export function listTenderDocuments(cookieHeader?: string, limit = 100) {
  return apiFetch<TenderDocumentSummary[]>(`/api/tender-documents?limit=${limit}`, undefined, cookieHeader);
}

export function getTenderDocument(id: string, cookieHeader?: string) {
  return apiFetch<TenderDocument>(`/api/tender-documents/${id}`, undefined, cookieHeader);
}

export function processTenderDocument(id: string, force = false) {
  return apiFetch<TenderDocument>(`/api/tender-documents/${id}/process`, {
    method: "POST",
    body: JSON.stringify({ force }),
  });
}
