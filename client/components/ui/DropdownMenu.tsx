"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/format";

/**
 * A small trigger + panel menu, following the same "wrap rather than
 * cloneElement" convention as FormDialog/ConfirmButton so triggers built in a
 * Server Component keep their nested icon types across the client boundary.
 */
export function DropdownMenu({
  trigger,
  children,
  align = "end",
}: {
  trigger: React.ReactElement<{ onClick?: () => void }>;
  children: React.ReactNode;
  align?: "start" | "end";
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative inline-block text-left">
      <span className="contents" onClick={() => setOpen((v) => !v)}>
        {trigger}
      </span>
      {open && (
        <div
          role="menu"
          className={cn(
            "absolute z-20 mt-1 w-48 overflow-hidden rounded-lg border border-line bg-surface py-1 shadow-lg",
            align === "end" ? "right-0" : "left-0",
          )}
          onClick={() => setOpen(false)}
        >
          {children}
        </div>
      )}
    </div>
  );
}

export function DropdownMenuItem({
  className,
  danger,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { danger?: boolean }) {
  return (
    <button
      type="button"
      role="menuitem"
      className={cn(
        "flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-left text-[13px] text-foreground transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50",
        danger && "text-danger",
        className,
      )}
      {...props}
    />
  );
}
