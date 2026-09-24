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
  programs: () => `/programs`,
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
  memberPurchases: (id: string) =>
    `/members/${id}/purchases${qs({ limit: 200 })}`,
  purchaseStats: (id: string, days?: number) =>
    `/members/${id}/purchase-stats${qs({ days })}`,
  memberChallenges: (id: string) =>
    `/members/${id}/challenges${qs({ limit: 200 })}`,
  tiers: () => `/tiers`,
  rewards: (activeOnly = false) =>
    `/rewards${qs({ limit: 1000, activeOnly })}`,
  products: (activeOnly = false) =>
    `/products${qs({ limit: 1000, activeOnly })}`,
  challenges: (activeOnly = false) =>
    `/challenges${qs({ limit: 1000, activeOnly })}`,
  segments: () => `/segments`,
  memberAttributes: () => `/member-attributes`,
  eventTypes: () => `/event-types`,
  eventType: (id: string) => `/event-types/${id}`,
  memberEvents: (id: string) => `/members/${id}/events${qs({ limit: 200 })}`,
} as const;
