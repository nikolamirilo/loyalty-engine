/**
 * Server-only client for the Loyalty Engine API.
 *
 * The bearer token is read from `API_TOKEN` (a non-public env var) and attached
 * on the server. This module must only be imported from Server Components and
 * Server Actions so the token is never sent to the browser.
 */
import type {
  Balance,
  Challenge,
  ChallengeAssignment,
  ChallengeStatus,
  Member,
  PointsTransaction,
  Redemption,
  RedemptionSource,
  Reward,
  Tier,
} from "./types";

const BASE_URL = (process.env.API_BASE_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);
const TOKEN = process.env.API_TOKEN ?? "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  /** JSON body — serialized and sent with the right Content-Type. */
  json?: unknown;
  /** Extra query params (undefined/null values are dropped). */
  query?: Record<string, string | number | boolean | undefined | null>;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(`${BASE_URL}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", json, query } = options;

  let res: Response;
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${TOKEN}`,
        ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: json !== undefined ? JSON.stringify(json) : undefined,
      // This is an admin console: always read fresh data from the API.
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      0,
      `Cannot reach the API at ${BASE_URL}. Make sure the server is running.`,
    );
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  let data: unknown = undefined;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, extractError(data, res.status));
  }

  return data as T;
}

/** FastAPI returns `{ detail: string }` or `{ detail: [{ msg, loc }] }`. */
function extractError(data: unknown, status: number): string {
  if (typeof data === "string" && data) return data;
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const msgs = detail
        .map((d) =>
          d && typeof d === "object" && "msg" in d
            ? String((d as { msg: unknown }).msg)
            : null,
        )
        .filter(Boolean);
      if (msgs.length) return msgs.join(", ");
    }
  }
  if (status === 401) return "Unauthorized — check the API_TOKEN configuration.";
  return `Request failed (${status}).`;
}

// ── Read helpers (used by Server Components) ─────────────────────────────────

export const getMembers = () =>
  apiRequest<Member[]>("/members", { query: { limit: 1000 } });

export const getMember = (id: string) => apiRequest<Member>(`/members/${id}`);

export const getBalance = (id: string) =>
  apiRequest<Balance>(`/members/${id}/balance`);

export const getTransactions = (id: string) =>
  apiRequest<PointsTransaction[]>(`/members/${id}/transactions`, {
    query: { limit: 200 },
  });

export const getRedemptions = (id: string) =>
  apiRequest<Redemption[]>(`/members/${id}/redemptions`, {
    query: { limit: 200 },
  });

export const getPrizes = (id: string, source?: RedemptionSource) =>
  apiRequest<Redemption[]>(`/members/${id}/prizes`, {
    query: { limit: 200, source },
  });

export const getMemberChallenges = (id: string, status?: ChallengeStatus) =>
  apiRequest<ChallengeAssignment[]>(`/members/${id}/challenges`, {
    query: { limit: 200, status },
  });

export const getRewards = (activeOnly = false) =>
  apiRequest<Reward[]>("/rewards", {
    query: { limit: 1000, active_only: activeOnly },
  });

export const getReward = (id: string) => apiRequest<Reward>(`/rewards/${id}`);

export const getChallenges = (activeOnly = false) =>
  apiRequest<Challenge[]>("/challenges", {
    query: { limit: 1000, active_only: activeOnly },
  });

export const getChallenge = (id: string) =>
  apiRequest<Challenge>(`/challenges/${id}`);

export const getTiers = () => apiRequest<Tier[]>("/tiers");
