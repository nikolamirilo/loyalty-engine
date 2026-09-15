import "server-only";

import { cookies } from "next/headers";

/**
 * Which program the current request addresses — SERVER ONLY.
 *
 * The API isolates every dataset by program and picks one from the
 * `X-Program-Id` header (a program slug or id). This resolves what that header
 * should say:
 *
 *  - the admin console sends whichever program the switcher last selected,
 *    stored in a cookie;
 *  - the member app has no switcher, so it serves the one program its
 *    deployment is pointed at (`MEMBER_PROGRAM`), which is how one demo gets
 *    its own URL;
 *  - when neither applies the header is omitted and the API falls back to its
 *    default program, which is what keeps a fresh install working.
 *
 * The cookie is not signed. The single admin credential may select any program
 * through the switcher anyway, so forging it grants nothing that clicking does
 * not. If per-program access control is ever added, this has to move into the
 * signed session token instead.
 */

export const PROGRAM_COOKIE = "admin_program";

/** The program a member-app deployment serves, if it is pointed at one. */
export function memberProgram(): string | undefined {
  const raw = process.env.MEMBER_PROGRAM?.trim();
  return raw ? raw : undefined;
}

export async function activeProgramId(): Promise<string | undefined> {
  const cookieStore = await cookies();
  return cookieStore.get(PROGRAM_COOKIE)?.value ?? memberProgram();
}
