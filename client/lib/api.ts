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
  ChallengeProgress,
  ChallengeStatus,
  Member,
  MemberProgram,
  PointsTransaction,
  Product,
  Program,
  Purchase,
  PurchaseStats,
  Redemption,
  RedemptionSource,
  Reward,
  Segment,
  Tier,
} from "./types";
import { UPSTREAM_BASE_URL as BASE_URL, UPSTREAM_TOKEN as TOKEN } from "@/lib/server/upstream";
import { activeProgramId } from "@/lib/server/program";

/** Max attempts (initial + retries). 3 = up to 2 retries on transient failure. */
const MAX_ATTEMPTS = 3;
/** Base delay for exponential backoff (ms). */
const RETRY_BASE_MS = 150;
/** Only retry transient failures (gateway issues, DB unavailable, our own 0). Not 500: retrying an API bug only delays the error. */
const RETRY_STATUSES = new Set([0, 502, 503, 504]);

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
  /** JSON body - serialized and sent with the right Content-Type. */
  json?: unknown;
  /** Raw binary body (a file upload), sent with the file's own Content-Type.
   *  Ignored when `json` is set. */
  file?: Blob;
  /** Extra query params (undefined/null values are dropped). */
  query?: Record<string, string | number | boolean | undefined | null>;
  /**
   * Program (slug or id) to scope this call to. Defaults to the active one for
   * the request, so the ~50 call sites in `lib/actions.ts` need not pass it.
   * Set it explicitly for calls that run before any session exists, and pass
   * `null` for the handful of endpoints that are not program-scoped
   * (`/programs` itself).
   */
  programId?: string | null;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  let url: URL;
  try {
    url = new URL(`${BASE_URL}${path}`);
  } catch {
    // A misconfigured API_BASE_URL would otherwise surface as a bare TypeError
    // from the URL constructor, which callers treat as "unexpected" and report
    // as a generic failure. Name the actual problem instead.
    throw new ApiError(
      0,
      `Invalid API base URL ${JSON.stringify(BASE_URL)} - check API_BASE_URL.`,
    );
  }
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** True if the status looks like a transient hiccup worth retrying. */
function isRetryable(status: number): boolean {
  return RETRY_STATUSES.has(status);
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", json, file, query, programId } = options;
  const url = buildUrl(path, query);
  // `null` means "deliberately unscoped"; `undefined` means "use the active
  // program", which is the common case.
  const program = programId === null ? undefined : programId ?? (await activeProgramId());
  const headers: Record<string, string> = {
    Accept: "application/json",
    Authorization: `Bearer ${TOKEN}`,
    ...(program ? { "X-Program-Id": program } : {}),
    ...(json !== undefined
      ? { "Content-Type": "application/json" }
      : file
        ? { "Content-Type": file.type || "application/octet-stream" }
        : {}),
  };
  const body = json !== undefined ? JSON.stringify(json) : file;

  let lastError: ApiError | null = null;

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    let res: Response;
    try {
      res = await fetch(url, {
        method,
        headers,
        body,
        // This is an admin console: always read fresh data from the API.
        cache: "no-store",
      });
    } catch {
      lastError = new ApiError(
        0,
        `Cannot reach the API at ${BASE_URL}. Make sure the server is running.`,
      );
      if (attempt < MAX_ATTEMPTS && isRetryable(0)) {
        await sleep(RETRY_BASE_MS * 2 ** (attempt - 1));
        continue;
      }
      throw lastError;
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

    if (res.ok) return data as T;

    const err = new ApiError(res.status, extractError(data, res.status));
    if (attempt < MAX_ATTEMPTS && isRetryable(res.status)) {
      lastError = err;
      await sleep(RETRY_BASE_MS * 2 ** (attempt - 1));
      continue;
    }
    throw err;
  }

  /* istanbul ignore next: unreachable, loop always returns or throws */
  throw lastError ?? new ApiError(0, "Request failed after retries.");
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
  if (status === 401) return "Unauthorized - check the API_TOKEN configuration.";
  return `Request failed (${status}).`;
}

// ── Read helpers (used by Server Components) ─────────────────────────────────

/** Not program-scoped: this is how the console discovers which programs exist. */
export const getPrograms = () =>
  apiRequest<Program[]>("/programs", { programId: null });

export const getMembers = () =>
  apiRequest<Member[]>("/members", { query: { limit: 1000 } });

/**
 * The member-facing app passes `programId` explicitly on these, because the
 * member and the console each select their own program and one person can be
 * signed into both at once (see lib/server/program.ts).
 */
export const getMember = (id: string, programId?: string) =>
  apiRequest<Member>(`/members/${id}`, { programId });

export const getMemberPrograms = (id: string, programId?: string) =>
  apiRequest<MemberProgram[]>(`/members/${id}/programs`, { programId });

export const getBalance = (id: string, programId?: string) =>
  apiRequest<Balance>(`/members/${id}/balance`, { programId });

export const getTransactions = (id: string) =>
  apiRequest<PointsTransaction[]>(`/members/${id}/transactions`, {
    query: { limit: 200 },
  });

export const getRedemptions = (id: string) =>
  apiRequest<Redemption[]>(`/members/${id}/redemptions`, {
    query: { limit: 200 },
  });

export const getPrizes = (
  id: string,
  source?: RedemptionSource,
  programId?: string,
) =>
  apiRequest<Redemption[]>(`/members/${id}/prizes`, {
    query: { limit: 200, source },
    programId,
  });

export const getMemberChallenges = (id: string, status?: ChallengeStatus) =>
  apiRequest<ChallengeAssignment[]>(`/members/${id}/challenges`, {
    query: { limit: 200, status },
  });

export const getRewards = (activeOnly = false) =>
  apiRequest<Reward[]>("/rewards", {
    query: { limit: 1000, activeOnly },
  });

export const getReward = (id: string) => apiRequest<Reward>(`/rewards/${id}`);

export const getProducts = (activeOnly = false, programId?: string) =>
  apiRequest<Product[]>("/products", {
    query: { limit: 1000, activeOnly },
    programId,
  });

export const getProduct = (id: string) => apiRequest<Product>(`/products/${id}`);

export const getMemberPurchases = (id: string, programId?: string) =>
  apiRequest<Purchase[]>(`/members/${id}/purchases`, {
    query: { limit: 200 },
    programId,
  });

export const getPurchaseStats = (
  id: string,
  days?: number,
  programId?: string,
) =>
  apiRequest<PurchaseStats>(`/members/${id}/purchase-stats`, {
    query: { days },
    programId,
  });

export const getChallenges = (activeOnly = false) =>
  apiRequest<Challenge[]>("/challenges", {
    query: { limit: 1000, activeOnly },
  });

export const getChallenge = (id: string) =>
  apiRequest<Challenge>(`/challenges/${id}`);

export const getChallengeProgress = (memberId: string, challengeId: string) =>
  apiRequest<ChallengeProgress>(`/members/${memberId}/challenges/${challengeId}`);

export const getTiers = () => apiRequest<Tier[]>("/tiers");

export const getSegments = () => apiRequest<Segment[]>("/segments");

export const getSegment = (id: string) => apiRequest<Segment>(`/segments/${id}`);
