import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

/**
 * Navigation skeleton for the member tab shell, mirroring the admin console's
 * loading.tsx. It sits inside the `(member)` segment, so Next wraps each tab's
 * page in a Suspense boundary *below* MemberShell - the header and tab bar stay
 * put and only the content area swaps while the page streams in.
 *
 * This file is also what makes the tabs prefetchable. Per Next's prefetching
 * rules, a dynamic route (all these tabs read the member session cookie) is
 * only prefetched down to its nearest loading boundary; without one, there is
 * nothing to prefetch and every tab switch waits on a full server round-trip.
 *
 * The shape (header + tile + list) matches Wallet, the busiest tab.
 */
export default function MemberLoading() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading">
      {/* Page header */}
      <div className="space-y-2.5">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-4 w-56" />
      </div>

      {/* Stat tile */}
      <Card className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-3">
            <Skeleton className="h-3.5 w-24" />
            <Skeleton className="h-8 w-20" />
          </div>
          <Skeleton className="h-10 w-10 rounded-lg" />
        </div>
      </Card>

      {/* List block */}
      <Card className="overflow-hidden">
        <div className="border-b border-line px-5 py-4 space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-3 w-48" />
        </div>
        <div className="divide-y divide-line">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-5 py-4">
              <Skeleton className="h-9 w-9 rounded-lg" />
              <div className="min-w-0 flex-1 space-y-2">
                <Skeleton className="h-4 w-36" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
