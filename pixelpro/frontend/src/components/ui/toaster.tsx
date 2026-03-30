"use client";
import { useState, useEffect } from "react";
import { X, CheckCircle2, AlertCircle } from "lucide-react";

type Toast = {
  id: string;
  message: string;
  type: "success" | "error" | "info";
};

let toastQueue: ((t: Toast) => void)[] = [];

export function toast(message: string, type: Toast["type"] = "info") {
  const t: Toast = { id: crypto.randomUUID(), message, type };
  toastQueue.forEach((fn) => fn(t));
}

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const fn = (t: Toast) => {
      setToasts((prev) => [...prev, t]);
      setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== t.id)), 4000);
    };
    toastQueue.push(fn);
    return () => { toastQueue = toastQueue.filter((f) => f !== fn); };
  }, []);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 rounded-xl px-4 py-3 shadow-lg text-sm font-medium max-w-sm ${
            t.type === "success" ? "bg-green-600 text-white" :
            t.type === "error" ? "bg-red-600 text-white" :
            "bg-gray-900 text-white"
          }`}
        >
          {t.type === "success" && <CheckCircle2 className="h-4 w-4 flex-shrink-0" />}
          {t.type === "error" && <AlertCircle className="h-4 w-4 flex-shrink-0" />}
          <span>{t.message}</span>
          <button onClick={() => setToasts((p) => p.filter((x) => x.id !== t.id))}>
            <X className="h-4 w-4 opacity-70 hover:opacity-100" />
          </button>
        </div>
      ))}
    </div>
  );
}
