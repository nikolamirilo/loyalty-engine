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

type Size = "md" | "sm";

const VALUE_SIZE: Record<Size, string> = {
  md: "mt-2 text-3xl",
  // Used where two tiles sit side by side with a longer value (e.g. a
  // currency amount) - the default text-3xl wraps or overflows the card at
  // that width.
  sm: "mt-1.5 text-xl",
};

const ICON_CHIP_SIZE: Record<Size, string> = {
  md: "h-10 w-10 text-xl",
  sm: "h-8 w-8 text-base",
};

const PADDING_SIZE: Record<Size, string> = {
  md: "p-5",
  sm: "p-4",
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
  size = "md",
}: {
  label: string;
  value: number | string;
  sub?: string;
  icon: React.ReactNode;
  accent?: Accent;
  size?: Size;
}) {
  return (
    <Card className={PADDING_SIZE[size]}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-muted">{label}</p>
          <p
            className={cn(
              "font-semibold tracking-tight text-foreground",
              VALUE_SIZE[size],
            )}
          >
            {typeof value === "number" ? compactNumber(value) : value}
          </p>
          {sub && <p className="mt-1 text-xs text-faint">{sub}</p>}
        </div>
        <div
          className={cn(
            "flex shrink-0 items-center justify-center rounded-lg",
            ICON_CHIP_SIZE[size],
            ACCENT_CHIP[accent],
          )}
        >
          {icon}
        </div>
      </div>
    </Card>
  );
}
