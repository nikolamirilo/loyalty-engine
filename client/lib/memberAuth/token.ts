import { createHmac, timingSafeEqual } from "node:crypto";

import { AUTH_SECRET } from "./config";

/**
 * Stateless member session tokens of the form
 * `<memberId>.<programId>.<expiresAtMs>.<hmac>`.
 *
 * Same shape and rationale as `lib/auth/token.ts`'s admin tokens (HMAC makes
 * it unforgeable, the embedded expiry makes it self-invalidating), plus the
 * member id so the app knows *who* is signed in without a server-side
 * session store.
 *
 * The program travels *inside* the token rather than beside it. A member id is
 * per program, so the two only mean something together: held in separate
 * cookies they get separate lifetimes, and the moment one outlives the other
 * every member-scoped read 404s with "Member not found". Signing them as one
 * payload makes that state unreachable.
 */

function sign(value: string): string {
  return createHmac("sha256", AUTH_SECRET).update(value).digest("hex");
}

export interface MemberSession {
  memberId: string;
  programId: string;
}

/** Create a signed token for a membership that expires at `expiresAtMs`. */
export function createMemberToken(
  memberId: string,
  programId: string,
  expiresAtMs: number,
): string {
  const payload = `${memberId}.${programId}.${expiresAtMs}`;
  return `${payload}.${sign(payload)}`;
}

/** The membership if `token` has a valid signature and has not expired, else null. */
export function verifyMemberToken(token: string | undefined | null): MemberSession | null {
  if (!token) return null;

  const lastDot = token.lastIndexOf(".");
  if (lastDot <= 0) return null;

  const payload = token.slice(0, lastDot);
  const signature = token.slice(lastDot + 1);

  const parts = payload.split(".");
  // Exactly `<memberId>.<programId>.<expiresAt>`. The older two-part token
  // carried no program, which is the state this format exists to rule out -
  // honouring one would keep a session alive that cannot say which program its
  // member id belongs to. Rejecting it costs those sessions a single re-login.
  if (parts.length !== 3) return null;

  const expiresAt = Number(parts[2]);
  if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) return null;

  const provided = Buffer.from(signature, "hex");
  const expected = Buffer.from(sign(payload), "hex");
  if (provided.length === 0 || provided.length !== expected.length) {
    return null;
  }

  try {
    if (!timingSafeEqual(provided, expected)) return null;
  } catch {
    return null;
  }

  return { memberId: parts[0], programId: parts[1] };
}
