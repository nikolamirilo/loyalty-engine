import { cn } from "@/lib/format";

type Tone = "primary" | "success" | "warning" | "danger";

// Fill carries state; the track is a lighter step of the same ramp (tone-on-tone).
const TRACK: Record<Tone, string> = {
  primary: "bg-primary-subtle",
  success: "bg-success-subtle",
  warning: "bg-warning-subtle",
  danger: "bg-danger-subtle",
};
const FILL: Record<Tone, string> = {
  primary: "bg-primary",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
};

export function ProgressMeter({
  value,
  max,
  tone = "primary",
  className,
}: {
  value: number;
  max: number;
  tone?: Tone;
  className?: string;
}) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <div
      className={cn("h-2 w-full overflow-hidden rounded-full", TRACK[tone], className)}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      <div
        className={cn("h-full rounded-full transition-[width]", FILL[tone])}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
