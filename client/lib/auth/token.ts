import { createHmac, timingSafeEqual } from "node:crypto";

import { AUTH_SECRET } from "./config";

/**
 * Stateless session tokens of the form `<expiresAtMs>.<hmac>`.
 *
 * The HMAC (keyed by AUTH_SECRET) makes the token unforgeable, and the embedded
 * expiry makes it self-invalidating — no server-side session store required.
 *
 * This module is deliberately free of `next/headers` so it can run inside the
 * proxy (which reads cookies straight off the request) as well as in Server
 * Components and Server Actions.
 */

function sign(value: string): string {
  return createHmac("sha256", AUTH_SECRET).update(value).digest("hex");
}

/** Create a signed token that expires at `expiresAtMs`. */
export function createToken(expiresAtMs: number): string {
  return `${expiresAtMs}.${sign(String(expiresAtMs))}`;
}

/** True only if `token` has a valid signature and has not expired. */
export function verifyToken(token: string | undefined | null): boolean {
  if (!token) return false;

  const dot = token.lastIndexOf(".");
  if (dot <= 0) return false;

  const expPart = token.slice(0, dot);
  const signature = token.slice(dot + 1);

  const expiresAt = Number(expPart);
  if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) return false;

  const provided = Buffer.from(signature, "hex");
  const expected = Buffer.from(sign(expPart), "hex");
  if (provided.length === 0 || provided.length !== expected.length) {
    return false;
  }

  try {
    return timingSafeEqual(provided, expected);
  } catch {
    return false;
  }
}
