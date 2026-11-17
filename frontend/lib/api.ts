import { BackendHealthResponse } from "./types";

/**
 * Checks backend health without exposing any credentials.
 * Uses cache: "no-store" for fresh serverless health verification.
 */
export async function checkBackendHealth(): Promise<BackendHealthResponse | null> {
  try {
    const res = await fetch("/api/health", {
      method: "GET",
      cache: "no-store",
    });

    if (!res.ok) {
      return null;
    }

    return (await res.json()) as BackendHealthResponse;
  } catch {
    return null;
  }
}

