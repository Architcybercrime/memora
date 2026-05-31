"use client";

import { Mic, Square } from "lucide-react";
import { useRef, useState } from "react";
import { cn } from "@/lib/cn";

interface Props {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

/**
 * Push-to-record button. Captures mic audio via MediaRecorder and ships it
 * to the backend's /voice/transcribe (faster-whisper) endpoint.
 */
export function VoiceButton({ onTranscript, disabled }: Props) {
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function start() {
    if (busy || recording) return;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
    chunksRef.current = [];
    mr.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data);
    mr.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      setBusy(true);
      try {
        const { transcribe } = await import("@/lib/api");
        const text = await transcribe(blob);
        if (text) onTranscript(text);
      } finally {
        setBusy(false);
      }
    };
    mediaRef.current = mr;
    mr.start();
    setRecording(true);
  }

  function stop() {
    mediaRef.current?.stop();
    setRecording(false);
  }

  return (
    <button
      type="button"
      disabled={disabled || busy}
      onClick={recording ? stop : start}
      className={cn(
        "h-10 w-10 grid place-items-center rounded-xl border border-border transition",
        recording ? "bg-red-500/20 border-red-500/60 text-red-300" : "bg-surface hover:bg-border",
        (disabled || busy) && "opacity-50 cursor-not-allowed",
      )}
      title={recording ? "Stop & transcribe" : "Record voice"}
    >
      {recording ? <Square size={16} /> : <Mic size={16} />}
    </button>
  );
}
