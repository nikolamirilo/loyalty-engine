import { createHmac, timingSafeEqual } from "node:crypto";

import { AUTH_SECRET } from "./config";

/**
 * Stateless member session tokens of the form `<memberId>.<expiresAtMs>.<hmac>`.
 *
 * Same shape and rationale as `lib/auth/token.ts`'s admin tokens (HMAC makes
 * it unforgeable, the embedded expiry makes it self-invalidating), plus the
 * member id so the app knows *who* is signed in without a server-side
 * session store.
 */

function sign(value: string): string {
  return createHmac("sha256", AUTH_SECRET).update(value).digest("hex");
}

/** Create a signed token for `memberId` that expires at `expiresAtMs`. */
export function createMemberToken(memberId: string, expiresAtMs: number): string {
  const payload = `${memberId}.${expiresAtMs}`;
  return `${payload}.${sign(payload)}`;
}

/** The member id if `token` has a valid signature and has not expired, else null. */
export function verifyMemberToken(token: string | undefined | null): string | null {
  if (!token) return null;

  const lastDot = token.lastIndexOf(".");
  if (lastDot <= 0) return null;

  const payload = token.slice(0, lastDot);
  const signature = token.slice(lastDot + 1);

  const dot = payload.lastIndexOf(".");
  if (dot <= 0) return null;

  const memberId = payload.slice(0, dot);
  const expPart = payload.slice(dot + 1);

  const expiresAt = Number(expPart);
  if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) return null;

  const provided = Buffer.from(signature, "hex");
  const expected = Buffer.from(sign(payload), "hex");
  if (provided.length === 0 || provided.length !== expected.length) {
    return null;
  }

  try {
    return timingSafeEqual(provided, expected) ? memberId : null;
  } catch {
    return null;
  }
}
