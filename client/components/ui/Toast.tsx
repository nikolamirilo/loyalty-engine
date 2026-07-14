"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/format";
import { CheckCircleIcon, InfoIcon, XCircleIcon, XIcon } from "./icons";

type Tone = "success" | "error" | "info";
type ToastItem = { id: number; tone: Tone; message: string };

type ToastApi = {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
};

const ToastContext = createContext<ToastApi | null>(null);

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within <ToastProvider>");
  return ctx;
}

let nextId = 1;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const remove = useCallback((id: number) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (tone: Tone, message: string) => {
      const id = nextId++;
      setToasts((list) => [...list, { id, tone, message }]);
      setTimeout(() => remove(id), 4500);
    },
    [remove],
  );

  const api: ToastApi = useMemo(
    () => ({
      success: (m) => push("success", m),
      error: (m) => push("error", m),
      info: (m) => push("info", m),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      {mounted &&
        createPortal(
          <div className="pointer-events-none fixed inset-x-0 bottom-0 z-[60] flex flex-col items-center gap-2 p-4 sm:items-end sm:p-6">
            {toasts.map((t) => (
              <ToastCard key={t.id} toast={t} onClose={() => remove(t.id)} />
            ))}
          </div>,
          document.body,
        )}
    </ToastContext.Provider>
  );
}

const TONE_STYLES: Record<Tone, { ring: string; icon: React.ReactNode }> = {
  success: {
    ring: "text-success",
    icon: <CheckCircleIcon />,
  },
  error: {
    ring: "text-danger",
    icon: <XCircleIcon />,
  },
  info: {
    ring: "text-primary",
    icon: <InfoIcon />,
  },
};

function ToastCard({
  toast,
  onClose,
}: {
  toast: ToastItem;
  onClose: () => void;
}) {
  const { ring, icon } = TONE_STYLES[toast.tone];
  return (
    <div className="pointer-events-auto flex w-full max-w-sm animate-dialog-in items-start gap-3 rounded-xl border border-line bg-surface px-4 py-3 shadow-lg">
      <span className={cn("mt-0.5 shrink-0 text-lg", ring)}>{icon}</span>
      <p className="min-w-0 flex-1 text-[13px] text-foreground">{toast.message}</p>
      <button
        type="button"
        onClick={onClose}
        aria-label="Dismiss"
        className="-mr-1 -mt-0.5 shrink-0 rounded p-1 text-faint transition-colors hover:text-foreground"
      >
        <XIcon className="text-sm" />
      </button>
    </div>
  );
}
