"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

const POLL_MS = 15_000;

/**
 * Keeps the Wallet's points balance current without a manual reload.
 *
 * Points are awarded API-side (campaign play, challenge completion, an admin
 * adjustment), so the app never finds out a balance changed - there is nothing
 * to subscribe to. Re-running the page's Server Components on a timer is the
 * cheapest way to notice, and it keeps the balance fetch on the server rather
 * than opening a member-authenticated data route to the browser.
 *
 * The refresh on mount is the load-bearing one: `staleTimes.dynamic` in
 * `next.config.ts` lets the client Router Cache serve an already-rendered
 * Wallet on tab switches, so arriving here straight from a campaign would
 * otherwise show a stale number. `router.refresh()` bypasses that cache.
 */
export function BalanceAutoRefresh() {
  const router = useRouter();
  const caughtUp = useRef(false);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;

    const stop = () => {
      if (timer) clearInterval(timer);
      timer = undefined;
    };
    const start = () => {
      stop();
      timer = setInterval(() => router.refresh(), POLL_MS);
    };

    // Guarded by a ref so this stays once-per-mount even if the effect is torn
    // down and re-run - refreshing on every re-run would loop.
    if (!caughtUp.current) {
      caughtUp.current = true;
      router.refresh();
    }

    // A backgrounded tab should not poll; coming back should catch up at once.
    const onVisibilityChange = () => {
      if (document.hidden) {
        stop();
        return;
      }
      router.refresh();
      start();
    };

    if (!document.hidden) start();
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [router]);

  return null;
}
