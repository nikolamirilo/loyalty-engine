import { cookies } from "next/headers";

import { SESSION_COOKIE, SESSION_TTL_MS } from "./config";
import { createToken, verifyToken } from "./token";

/** Issue a fresh session cookie on the outgoing response. */
export async function createSession(): Promise<void> {
  const expiresAt = Date.now() + SESSION_TTL_MS;
  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE, createToken(expiresAt), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    expires: new Date(expiresAt),
    path: "/",
  });
}

/** Clear the session cookie (logout). */
export async function destroySession(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE);
}

/** True if the current request carries a valid admin session. */
export async function isAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies();
  return verifyToken(cookieStore.get(SESSION_COOKIE)?.value);
}
