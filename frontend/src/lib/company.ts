// Frontend API client for company management.

import { getApiBaseUrl } from "@/lib/utils";

export interface CompanySummary {
  id: string;
  legal_name: string;
  display_name: string;
  legal_entity_type?: string | null;
  city?: string | null;
  state?: string | null;
  is_active: boolean;
  project_count: number;
  registration_count: number;
  document_count: number;
}

export interface Company extends CompanySummary {
  registration_number?: string | null;
  incorporation_date?: string | null;
  description?: string | null;
  registered_address?: string | null;
  office_address?: string | null;
  district?: string | null;
  pin_code?: string | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LookupItem {
  id: string;
  code: string;
  name: string;
  description?: string | null;
}

export interface Experience {
  id: string;
  company_id: string;
  project_name: string;
  work_category?: string | null;
  subcategory?: string | null;
  client_department?: string | null;
  state?: string | null;
  district?: string | null;
  contract_value?: string | null;
  project_status: string;
  is_active: boolean;
}

export interface CompanyCapability {
  id: string;
  company_id: string;
  capability_id: string;
  capability: LookupItem;
  years_of_experience?: number | null;
  experience_level?: string | null;
}

export interface CompanyDocument {
  id: string;
  company_id: string;
  document_type: LookupItem;
  original_filename: string;
  mime_type: string;
  file_size: number;
  document_status: string;
  expiry_date?: string | null;
  description?: string | null;
}

async function apiFetch<T>(path: string, init?: RequestInit, cookieHeader?: string): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (cookieHeader) headers.cookie = cookieHeader;

  const response = await fetch(`${getApiBaseUrl(Boolean(cookieHeader))}${path}`, {
    ...init,
    headers,
    credentials: cookieHeader ? undefined : "include",
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed." }));
    throw new Error(payload.detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function listCompanies(search?: string, activeOnly?: boolean, cookieHeader?: string) {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (activeOnly !== undefined) params.set("active_only", String(activeOnly));
  const query = params.toString();
  return apiFetch<CompanySummary[]>(`/api/companies${query ? `?${query}` : ""}`, undefined, cookieHeader);
}

export function getCompany(id: string, cookieHeader?: string) {
  return apiFetch<Company>(`/api/companies/${id}`, undefined, cookieHeader);
}

export function createCompany(payload: Partial<Company>, cookieHeader?: string) {
  return apiFetch<Company>(
    "/api/companies",
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export function updateCompany(id: string, payload: Partial<Company>, cookieHeader?: string) {
  return apiFetch<Company>(
    `/api/companies/${id}`,
    { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export function listExperiences(companyId: string, cookieHeader?: string) {
  return apiFetch<Experience[]>(`/api/companies/${companyId}/experiences`, undefined, cookieHeader);
}

export function createExperience(companyId: string, payload: Partial<Experience>, cookieHeader?: string) {
  return apiFetch<Experience>(
    `/api/companies/${companyId}/experiences`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export function listCapabilities(companyId: string, cookieHeader?: string) {
  return apiFetch<CompanyCapability[]>(`/api/companies/${companyId}/capabilities`, undefined, cookieHeader);
}

export function assignCapability(
  companyId: string,
  payload: { capability_id: string; years_of_experience?: number },
  cookieHeader?: string,
) {
  return apiFetch<CompanyCapability>(
    `/api/companies/${companyId}/capabilities`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) },
    cookieHeader,
  );
}

export function listDocuments(companyId: string, cookieHeader?: string) {
  return apiFetch<CompanyDocument[]>(`/api/companies/${companyId}/documents`, undefined, cookieHeader);
}

export function listDocumentTypes(cookieHeader?: string) {
  return apiFetch<LookupItem[]>("/api/companies/lookup/document-types", undefined, cookieHeader);
}

export function listCapabilityCategories(cookieHeader?: string) {
  return apiFetch<LookupItem[]>("/api/companies/lookup/capability-categories", undefined, cookieHeader);
}

export async function uploadDocument(
  companyId: string,
  file: File,
  documentTypeId: string,
  description?: string,
  cookieHeader?: string,
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type_id", documentTypeId);
  if (description) formData.append("description", description);

  const headers: Record<string, string> = {};
  if (cookieHeader) headers.cookie = cookieHeader;

  const response = await fetch(`${getApiBaseUrl(Boolean(cookieHeader))}/api/companies/${companyId}/documents`, {
    method: "POST",
    body: formData,
    headers,
    credentials: cookieHeader ? undefined : "include",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Upload failed." }));
    throw new Error(payload.detail || "Upload failed.");
  }

  return response.json() as Promise<CompanyDocument>;
}
