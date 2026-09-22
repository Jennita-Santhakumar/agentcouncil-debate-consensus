import type { DebateDetail, DebateSummary } from "./types";

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8100";
export const WS_BASE_URL: string =
  (import.meta.env.VITE_WS_BASE_URL as string | undefined) ?? "ws://localhost:8100";

async function handleJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Request failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function createDebate(topic: string, numRounds: number): Promise<{ debate_id: string }> {
  const res = await fetch(`${API_BASE_URL}/api/v1/debates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, num_rounds: numRounds }),
  });
  return handleJson(res);
}

export async function listDebates(): Promise<DebateSummary[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/debates`);
  return handleJson(res);
}

export async function getDebate(debateId: string): Promise<DebateDetail> {
  const res = await fetch(`${API_BASE_URL}/api/v1/debates/${debateId}`);
  return handleJson(res);
}

export function debateWebSocketUrl(debateId: string): string {
  return `${WS_BASE_URL}/ws/debate/${debateId}`;
}
