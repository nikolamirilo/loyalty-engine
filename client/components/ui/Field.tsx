import type {
  InputHTMLAttributes,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import { cn } from "@/lib/format";

const CONTROL =
  "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-foreground " +
  "placeholder:text-faint transition-colors focus:border-primary focus-visible:outline-none " +
  "focus:ring-2 focus:ring-primary/25 disabled:opacity-60";

export function Label({
  htmlFor,
  children,
  hint,
}: {
  htmlFor?: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-1.5 flex items-center justify-between gap-2 text-[13px] font-medium text-foreground"
    >
      <span>{children}</span>
      {hint && <span className="font-normal text-faint">{hint}</span>}
    </label>
  );
}

export function Field({
  label,
  htmlFor,
  hint,
  help,
  children,
  className,
}: {
  label?: string;
  htmlFor?: string;
  hint?: string;
  help?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      {label && (
        <Label htmlFor={htmlFor} hint={hint}>
          {label}
        </Label>
      )}
      {children}
      {help && <p className="mt-1 text-xs text-faint">{help}</p>}
    </div>
  );
}

export function Input({
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(CONTROL, className)} {...props} />;
}

export function Textarea({
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea className={cn(CONTROL, "min-h-19 resize-y", className)} {...props} />
  );
}

export function Select({
  className,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn(CONTROL, "cursor-pointer", className)} {...props} />;
}

export function Checkbox({
  label,
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex cursor-pointer items-center gap-2.5 text-sm text-foreground select-none">
      <input
        type="checkbox"
        className={cn(
          "h-4 w-4 rounded border-line text-primary accent-primary",
          className,
        )}
        {...props}
      />
      {label}
    </label>
  );
}
