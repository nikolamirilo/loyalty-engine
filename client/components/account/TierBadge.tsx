import type { Tier } from "@/lib/types";
import { AwardIcon } from "@/components/ui/icons";

/**
 * The member's current tier, as a gradient banner at the top of Account.
 *
 * Runs from the program's primary to its secondary brand colour, so a branded
 * program's banner is in its own colours (stock: violet to orange).
 *
 * Text is hardcoded white rather than `text-primary-fg`: that token inverts to
 * near-black in dark mode, which would be unreadable on this always-saturated
 * gradient.
 */
export function TierBadge({ tier }: { tier: Tier }) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary via-primary to-secondary p-5 text-white shadow-sm">
      {/* Soft corner highlight, so the gradient reads as a lit surface rather
          than a flat fill. */}
      <span
        aria-hidden
        className="pointer-events-none absolute -right-10 -top-12 h-32 w-32 rounded-full bg-white/20 blur-2xl"
      />

      <div className="relative flex items-center gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white/20 text-2xl">
          <AwardIcon />
        </span>
        <div className="min-w-0">
          <p className="text-[0.6875rem] font-medium uppercase tracking-wider text-white/80">
            Your tier
          </p>
          <p className="truncate text-xl font-semibold tracking-tight">{tier.name}</p>
        </div>
        {tier.multiplier > 1 && (
          <span className="ml-auto shrink-0 rounded-full bg-white/20 px-2.5 py-1 text-xs font-semibold">
            {tier.multiplier}x points
          </span>
        )}
      </div>
    </div>
  );
}
