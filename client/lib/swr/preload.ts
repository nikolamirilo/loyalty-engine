"use client";

import { preload } from "swr";

import { fetcher } from "./fetcher";
import { keys } from "./keys";

const warm = (key: string) => {
  void preload(key, fetcher);
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
