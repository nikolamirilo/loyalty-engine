/**
 * Member session configuration.
 *
 * Reuses `AUTH_SECRET` from the admin auth config (`@/lib/auth/config`) to
 * sign member session tokens - one secret, two independent token formats
 * (see `token.ts`), so an admin session and a member session can never be
 * mistaken for each other even though they share a signing key.
 */

export { AUTH_SECRET } from "@/lib/auth/config";

/** Name of the signed session cookie set on successful login/signup. */
export const MEMBER_SESSION_COOKIE = "member_session";

/** How long a signed-in member stays signed in (30 days). */
export const MEMBER_SESSION_TTL_MS = 30 * 24 * 60 * 60 * 1000;
