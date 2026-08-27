import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getServerApiBaseUrl(): string {
  return process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export function getBrowserApiBaseUrl(): string {
  return "";
}

export function getApiBaseUrl(isServer = typeof window === "undefined"): string {
  return isServer ? getServerApiBaseUrl() : getBrowserApiBaseUrl();
}
