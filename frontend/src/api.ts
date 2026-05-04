import type { ProcessDefinition, ProcessSummary, SaveProcessPayload } from "./types";

const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.error || body.detail || `HTTP ${resp.status}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export async function listProcesses(): Promise<ProcessSummary[]> {
  return request<ProcessSummary[]>("/processes");
}

export async function getProcess(id: string): Promise<ProcessDefinition> {
  return request<ProcessDefinition>(`/processes/${id}`);
}

export async function createProcess(payload: SaveProcessPayload): Promise<ProcessSummary> {
  return request<ProcessSummary>("/processes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateProcess(id: string, payload: SaveProcessPayload): Promise<ProcessSummary> {
  return request<ProcessSummary>(`/processes/${id}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteProcess(id: string): Promise<void> {
  return request<void>(`/processes/${id}`, { method: "DELETE" });
}
