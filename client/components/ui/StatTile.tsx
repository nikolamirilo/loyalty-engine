import { compactNumber, cn } from "@/lib/format";
import { Card } from "./Card";

export type Accent = "blue" | "aqua" | "violet" | "orange" | "yellow";

// Literal class names so Tailwind's scanner can see them (no dynamic strings).
const ACCENT_CHIP: Record<Accent, string> = {
  blue: "bg-accent-blue/12 text-accent-blue",
  aqua: "bg-accent-aqua/15 text-accent-aqua",
  violet: "bg-accent-violet/12 text-accent-violet",
  orange: "bg-accent-orange/12 text-accent-orange",
  yellow: "bg-accent-yellow/15 text-accent-yellow",
};

/**
 * Stat tile per the data-viz figure contract: sentence-case label, a semibold
 * value (auto-compact, proportional figures), and an accent icon chip. The
 * label + icon always accompany the color, so the accent never carries meaning
 * alone (satisfies the relief rule for the sub-3:1 aqua accent in light mode).
 */
export function StatTile({
  label,
  value,
  sub,
  icon,
  accent = "blue",
}: {
  label: string;
  value: number | string;
  sub?: string;
  icon: React.ReactNode;
  accent?: Accent;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-muted">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight text-foreground">
            {typeof value === "number" ? compactNumber(value) : value}
          </p>
          {sub && <p className="mt-1 text-xs text-faint">{sub}</p>}
        </div>
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-xl",
            ACCENT_CHIP[accent],
          )}
        >
          {icon}
        </div>
      </div>
    </Card>
  );
}
