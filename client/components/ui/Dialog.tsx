"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/format";
import { useMounted } from "@/lib/use-mounted";
import { XIcon } from "./icons";

const SIZES = {
  sm: "max-w-sm",
  md: "max-w-lg",
  lg: "max-w-2xl",
};

export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  size = "md",
  align = "start",
  scrollBody = false,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  size?: keyof typeof SIZES;
  /** `start` (default) hangs the panel from the top, which keeps a long admin
   *  form scrollable from its first field. `center` puts it on the middle of
   *  the screen - what a phone-sized sheet wants. */
  align?: "start" | "center";
  /** Cap the panel at the viewport and scroll its body instead, so content
   *  that grows while the dialog is open (rows added to a builder) never
   *  pushes the panel off the bottom of the screen. The title stays put. */
  scrollBody?: boolean;
}) {
  // createPortal needs document, which does not exist while rendering on the
  // server.
  const mounted = useMounted();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!mounted || !open) return null;

  return createPortal(
    <div
      className={cn(
        "fixed inset-0 z-50 flex justify-center overflow-y-auto p-4 sm:p-6",
        align === "center" ? "items-center" : "items-start",
      )}
    >
      <div
        className="fixed inset-0 animate-fade-in bg-black/40 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          "relative z-10 my-6 w-full animate-dialog-in rounded-2xl border border-line bg-surface shadow-xl",
          SIZES[size],
          // The overlay's padding plus this panel's my-6, top and bottom.
          scrollBody && "flex max-h-[calc(100dvh-5rem)] flex-col sm:max-h-[calc(100dvh-6rem)]",
        )}
      >
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-foreground">{title}</h2>
            {description && (
              <p className="mt-0.5 text-[0.8125rem] text-muted">{description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="-mr-1.5 -mt-1 flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg text-lg text-faint transition-colors hover:bg-surface-2 hover:text-foreground"
          >
            <XIcon />
          </button>
        </div>
        <div className={cn("px-5 py-4", scrollBody && "min-h-0 overflow-y-auto")}>{children}</div>
      </div>
    </div>,
    document.body,
  );
}
