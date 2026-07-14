import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/format";
import { Spinner } from "./Spinner";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "success";
type Size = "sm" | "md" | "icon";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-primary text-primary-fg hover:bg-primary-hover shadow-sm disabled:hover:bg-primary",
  secondary:
    "bg-surface text-foreground border border-line hover:bg-surface-2 disabled:hover:bg-surface",
  ghost: "text-muted hover:bg-surface-2 hover:text-foreground",
  danger:
    "bg-danger text-white hover:brightness-95 shadow-sm disabled:hover:brightness-100",
  success: "bg-success text-white hover:brightness-95 shadow-sm",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-[13px] gap-1.5 rounded-lg",
  md: "h-10 px-4 text-sm gap-2 rounded-lg",
  icon: "h-9 w-9 rounded-lg justify-center",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium whitespace-nowrap transition-colors select-none cursor-pointer",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      type="button"
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner className="text-base" />}
      {children}
    </button>
  );
}
