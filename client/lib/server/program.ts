import "server-only";

import { cookies } from "next/headers";

import { getMemberSession } from "@/lib/memberAuth/session";

/**
 * Which program a request addresses — SERVER ONLY.
 *
 * The API isolates every dataset by program and picks one from the
 * `X-Program-Id` header (a program slug or id). The two surfaces choose it
 * independently, and each has its own cookie, because one person can be signed
 * into both at once while looking at different programs:
 *
 *  - the console sends whatever its sidebar switcher last selected;
 *  - the member app sends whatever the account page last selected, falling
 *    back to `MEMBER_PROGRAM` so a deployment can be pinned to one demo.
 *
 * Neither cookie is signed. Both surfaces let you pick any program through the
 * UI anyway, so forging one grants nothing that clicking does not. If
 * per-program access control is ever added, these have to move into the signed
 * session tokens instead.
 */

export const PROGRAM_COOKIE = "admin_program";
export const MEMBER_PROGRAM_COOKIE = "member_program";

/** The program a member-app deployment is pinned to, if any. */
export function memberProgram(): string | undefined {
  const raw = process.env.MEMBER_PROGRAM?.trim();
  return raw ? raw : undefined;
}

/** The console's selected program. */
export async function activeProgramId(): Promise<string | undefined> {
  const cookieStore = await cookies();
  return cookieStore.get(PROGRAM_COOKIE)?.value ?? memberProgram();
}

/**
 * The signed-in member's program.
 *
 * The session token is asked first and believed absolutely: it carries the
 * program its member id belongs to, signed into the same payload, so the pair
 * cannot disagree. The cookie is what remains for everyone *without* a session
 * - it is how the login and signup pages choose which program to authenticate
 * against - and the fallback pins a deployment to one program.
 */
export async function memberProgramId(): Promise<string | undefined> {
  const session = await getMemberSession();
  if (session) return session.programId;

  const cookieStore = await cookies();
  return cookieStore.get(MEMBER_PROGRAM_COOKIE)?.value ?? memberProgram();
}
