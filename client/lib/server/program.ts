import "server-only";

import { cookies } from "next/headers";

import { getMemberSession } from "@/lib/memberAuth/session";

/**
 * Which program a request addresses — SERVER ONLY.
 *
 * The API isolates every dataset by program and picks one from the
 * `X-Program-Id` header (a program slug or id). The two surfaces choose it
 * independently, because one person can be signed into both at once while
 * looking at different programs:
 *
 *  - the console sends whatever its sidebar switcher last selected (a cookie);
 *  - the member app sends the program in the member's session. Every member
 *    belongs to every program and signing in always lands in the default one,
 *    so a member without a session has no program at all - sign-in and email
 *    verification are person-level and never send one.
 *
 * The console cookie is not signed. The UI lets you pick any program anyway,
 * so forging it grants nothing that clicking does not. If per-program access
 * control is ever added, it has to move into the signed session token instead.
 */

export const PROGRAM_COOKIE = "admin_program";

/** The console's selected program. */
export async function activeProgramId(): Promise<string | undefined> {
  const cookieStore = await cookies();
  return cookieStore.get(PROGRAM_COOKIE)?.value;
}

/**
 * The signed-in member's program, straight from the session token: it carries
 * the program its member id belongs to, signed into the same payload, so the
 * pair cannot disagree. `undefined` without a session - callers fall back to
 * the default program, which is where sign-in lands.
 */
export async function memberProgramId(): Promise<string | undefined> {
  const session = await getMemberSession();
  return session?.programId;
}
