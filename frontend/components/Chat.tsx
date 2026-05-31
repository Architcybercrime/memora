"use client";

import { Brain, Eraser, Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { clearSession, streamChat } from "@/lib/api";
import { cn } from "@/lib/cn";
import { MemoryDrawer } from "./MemoryDrawer";
import { VoiceButton } from "./VoiceButton";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

const USER_ID_KEY = "memora.userId";
const SESSION_ID_KEY = "memora.sessionId";

function getOrInit(key: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  let v = localStorage.getItem(key);
  if (!v) {
    v = fallback;
    localStorage.setItem(key, v);
  }
  return v;
}

export function Chat() {
  const [userId, setUserId] = useState("default");
  const [sessionId, setSessionId] = useState("default");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setUserId(getOrInit(USER_ID_KEY, crypto.randomUUID()));
    setSessionId(getOrInit(SESSION_ID_KEY, crypto.randomUUID()));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    const msg = text.trim();
    if (!msg || streaming) return;
    setInput("");
    setMessages((p) => [...p, { role: "user", content: msg }, { role: "assistant", content: "" }]);
    setStreaming(true);
    try {
      for await (const ev of streamChat({ user_id: userId, session_id: sessionId, message: msg })) {
        if (ev.kind === "token") {
          setMessages((prev) => {
            const copy = [...prev];
            copy[copy.length - 1] = { role: "assistant", content: copy[copy.length - 1].content + ev.text };
            return copy;
          });
        } else if (ev.kind === "error") {
          setMessages((prev) => {
            const copy = [...prev];
            copy[copy.length - 1] = { role: "assistant", content: `⚠️ ${ev.text}` };
            return copy;
          });
        }
      }
    } catch (e) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = { role: "assistant", content: `⚠️ ${(e as Error).message}` };
        return copy;
      });
    } finally {
      setStreaming(false);
    }
  }

  async function onClear() {
    await clearSession(userId, sessionId);
    setMessages([]);
  }

  return (
    <div className="h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent/20 grid place-items-center text-accent font-bold">M</div>
          <div>
            <div className="font-semibold leading-tight">Memora</div>
            <div className="text-xs text-muted leading-tight">user: {userId.slice(0, 8)}</div>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setDrawer(true)}
            className="px-3 h-9 inline-flex items-center gap-2 rounded-lg border border-border hover:bg-surface text-sm"
          >
            <Brain size={14} /> Memories
          </button>
          <button
            onClick={onClear}
            className="px-3 h-9 inline-flex items-center gap-2 rounded-lg border border-border hover:bg-surface text-sm"
          >
            <Eraser size={14} /> Clear session
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-muted mt-20">
              <Brain size={28} className="mx-auto mb-2 opacity-50" />
              <p>Hi. Tell me about yourself — I&apos;ll remember it across sessions.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={cn(
                "rounded-2xl px-4 py-3 max-w-[85%] whitespace-pre-wrap leading-relaxed",
                m.role === "user"
                  ? "ml-auto bg-accent/90 text-white"
                  : "bg-surface border border-border",
              )}
            >
              {m.content || <span className="text-muted">…</span>}
            </div>
          ))}
          <div ref={endRef} />
        </div>
      </main>

      <footer className="border-t border-border px-6 py-3">
        <div className="max-w-3xl mx-auto flex gap-2 items-end">
          <VoiceButton onTranscript={(t) => setInput((p) => (p ? p + " " + t : t))} disabled={streaming} />
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send(input);
              }
            }}
            placeholder="Message Memora…"
            rows={1}
            className="flex-1 resize-none rounded-xl bg-surface border border-border px-3 py-2 outline-none focus:border-accent text-sm"
          />
          <button
            onClick={() => void send(input)}
            disabled={!input.trim() || streaming}
            className="h-10 px-4 rounded-xl bg-accent text-white text-sm font-medium hover:opacity-90 disabled:opacity-40 inline-flex items-center gap-2"
          >
            <Send size={14} /> Send
          </button>
        </div>
      </footer>

      <MemoryDrawer userId={userId} open={drawer} onClose={() => setDrawer(false)} />
    </div>
  );
}
