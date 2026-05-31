// Client helpers for the Memora backend.

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Memory {
  id: number;
  user_id: string;
  content: string;
  context: string | null;
  category: string;
  importance: number;
  created_at: string;
  updated_at: string;
  access_count: number;
  last_used_at: string | null;
  score?: number | null;
}

/**
 * Stream a chat turn over SSE. Returns an async iterable of text tokens.
 * Caller is responsible for accumulating them.
 */
export async function* streamChat(
  params: { user_id: string; session_id: string; message: string },
  signal?: AbortSignal,
): AsyncGenerator<{ kind: "token" | "done" | "error"; text: string }> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`chat request failed: ${res.status}`);
  }
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    // SSE events are separated by blank lines.
    const events = buf.split("\n\n");
    buf = events.pop() ?? "";
    for (const evt of events) {
      const lines = evt.split("\n");
      let event = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      try {
        const parsed = JSON.parse(data);
        if (event === "token" && parsed.text) yield { kind: "token", text: parsed.text };
        else if (event === "done") yield { kind: "done", text: parsed.final ?? "" };
        else if (event === "error") yield { kind: "error", text: parsed.message ?? "error" };
      } catch {
        // ignore malformed
      }
    }
  }
}

export async function transcribe(blob: Blob): Promise<string> {
  const fd = new FormData();
  fd.append("audio", blob, "clip.webm");
  const res = await fetch(`${API_URL}/voice/transcribe`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`transcribe failed: ${res.status}`);
  const j = await res.json();
  return j.text as string;
}

export async function listMemories(userId: string): Promise<Memory[]> {
  const res = await fetch(`${API_URL}/memories/${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error(`list failed: ${res.status}`);
  return res.json();
}

export async function deleteMemory(userId: string, id: number): Promise<void> {
  const res = await fetch(`${API_URL}/memories/${encodeURIComponent(userId)}/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`delete failed: ${res.status}`);
}

export async function clearSession(userId: string, sessionId: string): Promise<void> {
  await fetch(`${API_URL}/chat/${encodeURIComponent(userId)}/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
}
