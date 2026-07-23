/**
 * Centralized SWR cache keys. Each key is the upstream API path + query string
 * (the fetcher prefixes `/api/le`). Keeping every key in one place keeps the
 * data flow consistent and makes cache invalidation predictable.
 */

type QueryValue = string | number | boolean | undefined | null;

function qs(params: Record<string, QueryValue>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const serialized = search.toString();
  return serialized ? `?${serialized}` : "";
}

export const keys = {
  members: ({
    skip,
    limit = 1000,
    q,
  }: { skip?: number; limit?: number; q?: string } = {}) =>
    `/members${qs({ skip, limit, q })}`,
  membersCount: (q?: string) => `/members/count${qs({ q })}`,
  memberStats: () => `/members/stats`,
  member: (id: string) => `/members/${id}`,
  balance: (id: string) => `/members/${id}/balance`,
  transactions: (id: string) =>
    `/members/${id}/transactions${qs({ limit: 200 })}`,
  redemptions: (id: string) =>
    `/members/${id}/redemptions${qs({ limit: 200 })}`,
  memberChallenges: (id: string) =>
    `/members/${id}/challenges${qs({ limit: 200 })}`,
  tiers: () => `/tiers`,
  rewards: (activeOnly = false) =>
    `/rewards${qs({ limit: 1000, active_only: activeOnly })}`,
  challenges: (activeOnly = false) =>
    `/challenges${qs({ limit: 1000, active_only: activeOnly })}`,
  segments: () => `/segments`,
} as const;
