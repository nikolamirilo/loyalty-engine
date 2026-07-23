import { LOCKOUT_MS, MAX_ATTEMPTS } from "./config";

/**
 * In-memory, per-IP failed-login tracking with a timed lockout.
 *
 * The store hangs off `globalThis` so the counter survives dev hot-reloads.
 * It's intentionally process-local (not shared with the proxy, per Next.js
 * guidance) and resets on restart - acceptable for a single-instance console.
 */

type Attempt = { fails: number; lockedUntil: number };

const globalStore = globalThis as unknown as {
  __adminLoginAttempts?: Map<string, Attempt>;
};

const store: Map<string, Attempt> = (globalStore.__adminLoginAttempts ??=
  new Map());

/** Drop entries that no longer hold any state, to bound memory growth. */
function prune(now: number): void {
  for (const [ip, attempt] of store) {
    if (attempt.fails === 0 && attempt.lockedUntil <= now) store.delete(ip);
  }
}

/** Milliseconds left on an active lockout for `ip` (0 if not locked). */
export function lockRemainingMs(ip: string): number {
  const remaining = (store.get(ip)?.lockedUntil ?? 0) - Date.now();
  return remaining > 0 ? remaining : 0;
}

export type FailureResult = {
  locked: boolean;
  remainingMs: number;
  attemptsLeft: number;
};

/**
 * Record a failed login for `ip`. On reaching MAX_ATTEMPTS this starts a
 * lockout and resets the counter, so a fresh batch of attempts is available
 * once the lockout expires.
 */
export function registerFailure(ip: string): FailureResult {
  const now = Date.now();
  prune(now);

  const attempt = store.get(ip) ?? { fails: 0, lockedUntil: 0 };

  // A previous lockout has elapsed - start counting fresh.
  if (attempt.lockedUntil && attempt.lockedUntil <= now) {
    attempt.fails = 0;
    attempt.lockedUntil = 0;
  }

  attempt.fails += 1;

  if (attempt.fails >= MAX_ATTEMPTS) {
    attempt.fails = 0;
    attempt.lockedUntil = now + LOCKOUT_MS;
    store.set(ip, attempt);
    return { locked: true, remainingMs: LOCKOUT_MS, attemptsLeft: 0 };
  }

  store.set(ip, attempt);
  return {
    locked: false,
    remainingMs: 0,
    attemptsLeft: MAX_ATTEMPTS - attempt.fails,
  };
}

/** Clear all recorded failures for `ip` (call on successful login). */
export function clearAttempts(ip: string): void {
  store.delete(ip);
}
