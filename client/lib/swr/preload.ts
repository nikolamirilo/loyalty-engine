"use client";

import { preload } from "swr";

import { fetcher } from "./fetcher";
import { keys } from "./keys";

const warm = (key: string) => {
  // Best-effort: this only warms the cache ahead of navigation, and the page's
  // own useSWR hook re-fetches (and surfaces real errors) on mount regardless.
  // Swallow failures here so a transient/aborted prefetch never becomes an
  // unhandled rejection.
  void preload(key, fetcher).catch(() => {});
};

/**
 * Warm the SWR cache for a route's data ahead of navigation (e.g. on nav-link
 * hover), so the page is usually already populated by the time it mounts. Keys
 * match the ones the pages' hooks use, so SWR dedupes rather than refetching.
 */
export const preloadRoute = {
  dashboard: () => {
    warm(keys.memberStats());
    warm(keys.tiers());
    warm(keys.rewards());
    warm(keys.challenges());
    warm(keys.members({ limit: 6 }));
  },
  members: () => {
    warm(keys.members({ skip: 0, limit: 10 }));
    warm(keys.membersCount());
    warm(keys.tiers());
    warm(keys.segments());
  },
  rewards: () => {
    warm(keys.rewards());
  },
  challenges: () => {
    warm(keys.challenges());
    warm(keys.rewards());
  },
  tiers: () => {
    warm(keys.tiers());
    warm(keys.memberStats());
  },
  segments: () => {
    warm(keys.segments());
    // Also warm the full member list the "Assign members" dialog reads, so
    // it's usually already cached by the time a segment card's dialog opens.
    warm(keys.members());
  },
};

/**
 * Warm a single member's detail data on row hover. Shared resources (tiers,
 * rewards, challenges) are typically already cached from navigation, so only
 * the member-specific keys are warmed here.
 */
export function preloadMember(id: string) {
  warm(keys.member(id));
  warm(keys.transactions(id));
  warm(keys.redemptions(id));
  warm(keys.memberChallenges(id));
}
