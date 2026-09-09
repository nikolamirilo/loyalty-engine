import { cookies } from "next/headers";

import { MEMBER_SESSION_COOKIE, MEMBER_SESSION_TTL_MS } from "./config";
import { createMemberToken, verifyMemberToken } from "./token";

/** Issue a fresh session cookie for `memberId` on the outgoing response. */
export async function createMemberSession(memberId: string): Promise<void> {
  const expiresAt = Date.now() + MEMBER_SESSION_TTL_MS;
  const cookieStore = await cookies();
  cookieStore.set(MEMBER_SESSION_COOKIE, createMemberToken(memberId, expiresAt), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    expires: new Date(expiresAt),
    path: "/",
  });
}

/** Clear the member session cookie (sign out). */
export async function destroySession(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(MEMBER_SESSION_COOKIE);
}

/** The signed-in member's id, or null if there is no valid session. */
export async function getSessionMemberId(): Promise<string | null> {
  const cookieStore = await cookies();
  return verifyMemberToken(cookieStore.get(MEMBER_SESSION_COOKIE)?.value);
}
