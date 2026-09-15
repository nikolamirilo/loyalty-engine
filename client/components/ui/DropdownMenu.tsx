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
  className,
  panelClassName,
}: {
  trigger: React.ReactElement<{ onClick?: () => void }>;
  children: React.ReactNode;
  align?: "start" | "end";
  /** Replaces the root's default `inline-block` - e.g. `block` for a
   *  full-width trigger. */
  className?: string;
  /** Replaces the panel's default `w-48`, for a menu that should match the
   *  width of what opened it. */
  panelClassName?: string;
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
    // The overrides replace their defaults rather than adding to them: `cn`
    // joins classes without resolving Tailwind conflicts, so an appended
    // `w-full` next to `w-48` would leave the winner up to stylesheet order.
    <div ref={ref} className={cn("relative text-left", className ?? "inline-block")}>
      <span className="contents" onClick={() => setOpen((v) => !v)}>
        {trigger}
      </span>
      {open && (
        <div
          role="menu"
          className={cn(
            "absolute z-20 mt-1 overflow-hidden rounded-lg border border-line bg-surface py-1 shadow-lg",
            align === "end" ? "right-0" : "left-0",
            panelClassName ?? "w-48",
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
        "flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-left text-[0.8125rem] text-foreground transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-50",
        danger && "text-danger",
        className,
      )}
      {...props}
    />
  );
}
