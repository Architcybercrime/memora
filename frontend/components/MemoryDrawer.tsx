"use client";

import { Brain, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { deleteMemory, listMemories, type Memory } from "@/lib/api";

interface Props {
  userId: string;
  open: boolean;
  onClose: () => void;
}

export function MemoryDrawer({ userId, open, onClose }: Props) {
  const [items, setItems] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setItems(await listMemories(userId));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open) void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, userId]);

  async function onDelete(id: number) {
    await deleteMemory(userId, id);
    setItems((prev) => prev.filter((m) => m.id !== id));
  }

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/50" onClick={onClose} />
      <aside className="w-[420px] bg-surface border-l border-border flex flex-col">
        <header className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Brain size={18} className="text-accent" />
            <h2 className="font-semibold">Long-term memory</h2>
            <span className="text-xs text-muted">({items.length})</span>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-border rounded">
            <X size={16} />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {loading && <div className="text-sm text-muted p-3">Loading…</div>}
          {!loading && items.length === 0 && (
            <div className="text-sm text-muted p-3">No memories yet. Tell the agent something about yourself.</div>
          )}
          {items.map((m) => (
            <div key={m.id} className="rounded-lg border border-border bg-bg p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="text-sm">{m.content}</div>
                <button
                  onClick={() => onDelete(m.id)}
                  className="text-muted hover:text-red-400 p-1"
                  title="Forget this"
                >
                  <Trash2 size={14} />
                </button>
              </div>
              {m.context && <div className="mt-1 text-xs text-muted italic">{m.context}</div>}
              <div className="mt-2 flex gap-2 text-[10px] uppercase tracking-wide text-muted">
                <span className="px-1.5 py-0.5 rounded bg-border">{m.category}</span>
                <span className="px-1.5 py-0.5 rounded bg-border">imp {m.importance.toFixed(2)}</span>
                <span className="ml-auto">{new Date(m.created_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}
