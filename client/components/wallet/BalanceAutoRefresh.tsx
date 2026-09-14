"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

/**
 * Keeps the Wallet's points balance current without a manual reload.
 *
 * Points are awarded API-side (campaign play, challenge completion, an admin
 * adjustment), so the app never finds out a balance changed - there is nothing
 * to subscribe to. Re-running the page's Server Components is the cheapest way
 * to notice, and it keeps the balance fetch on the server rather than opening a
 * member-authenticated data route to the browser.
 *
 * Event-driven rather than polled, deliberately: `router.refresh()` invalidates
 * the whole client Router Cache, layouts included, so the `(member)` layout has
 * to refetch and `MemberShell` remounts - tearing down the campaign iframe it
 * keeps mounted across tab switches. Refreshing only on arrival and on return
 * to the tab covers the flow that matters (play a campaign, then open Wallet)
 * without that cost.
 *
 * The refresh on arrival is the load-bearing one: `staleTimes.dynamic` in
 * `next.config.ts` lets the Router Cache serve an already-rendered Wallet on
 * tab switches, so coming straight from a campaign would otherwise show a
 * stale number. `router.refresh()` bypasses that cache.
 */
export function BalanceAutoRefresh() {
  const router = useRouter();
  const refreshedOnMount = useRef(false);
  const lastRefreshAt = useRef(0);

  useEffect(() => {
    // Returning to a backgrounded tab fires `visibilitychange` and `focus`
    // both; this collapses them into a single round-trip.
    const refresh = () => {
      if (document.hidden) return;
      const now = Date.now();
      if (now - lastRefreshAt.current < 1_000) return;
      lastRefreshAt.current = now;
      router.refresh();
    };

    // Separate guard from the dedupe window above: this one must hold for the
    // life of the mount, so a re-run of the effect can never start a refresh
    // loop no matter how long the refresh takes.
    if (!refreshedOnMount.current) {
      refreshedOnMount.current = true;
      refresh();
    }

    document.addEventListener("visibilitychange", refresh);
    window.addEventListener("focus", refresh);

    return () => {
      document.removeEventListener("visibilitychange", refresh);
      window.removeEventListener("focus", refresh);
    };
  }, [router]);

  return null;
}
