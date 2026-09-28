import { compactNumber } from "@/lib/format";
import { CoinsIcon } from "@/components/ui/icons";

/**
 * The member's points balance - the number a loyalty app is about - as a
 * brand surface at the top of Wallet, styled like the tier banner on Account
 * (components/account/TierBadge.tsx): stock it is the violet to orange
 * gradient, a branded program's is solid primary with secondary text.
 */
export function PointsCard({ points }: { points: number }) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary via-primary to-brand-card-end p-5 text-brand-card-fg shadow-sm">
      {/* Soft corner highlight, as on the tier banner. */}
      <span
        aria-hidden
        className="pointer-events-none absolute -right-10 -top-12 h-32 w-32 rounded-full bg-white/20 blur-2xl"
      />
      <div className="relative flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[0.6875rem] font-medium uppercase tracking-wider text-brand-card-fg/80">
            Points balance
          </p>
          <p className="mt-1 text-3xl font-semibold tracking-tight">{compactNumber(points)}</p>
        </div>
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brand-card-fg/20 text-2xl">
          <CoinsIcon />
        </span>
      </div>
    </div>
  );
}
