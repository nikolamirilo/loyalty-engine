"use client";

import { useSWRConfig } from "swr";

/**
 * Central cache-invalidation helpers for mutations. Since pages read through
 * SWR, a Server Action's `revalidatePath` no longer refreshes what the user
 * sees — after a successful write, call the matching helper to revalidate the
 * affected keys. Each helper matches every cache key under a resource prefix
 * (e.g. "/members" also covers "/members/:id" and its sub-resources).
 */
export function useRevalidate() {
  const { mutate } = useSWRConfig();

  const byPrefix = (prefix: string) =>
    mutate((key) => typeof key === "string" && key.startsWith(prefix));

  return {
    members: () => byPrefix("/members"),
    rewards: () => byPrefix("/rewards"),
    challenges: () => byPrefix("/challenges"),
    tiers: () => byPrefix("/tiers"),
  };
}
