"use server";

import type { ActionState } from "@/lib/action-state";
import { ApiError, apiRequest } from "@/lib/api";

/**
 * Server Action behind the public /verify page (the DOI `type: "link"` flow).
 *
 * The member arrives from an email link and is not signed in, so the call to
 * the API cannot go through the session-gated /api/le proxy. It runs here
 * instead: the bearer token stays on the server, and the only thing the caller
 * controls is the member id + code pair the API already validates - a wrong
 * pair is rejected there, and burns one of the member's five attempts.
 */
export async function verifyMemberEmail(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const memberId = String(fd.get("memberId") ?? "").trim();
  const code = String(fd.get("code") ?? "").trim();

  if (!memberId || !code) {
    return { ok: false, error: "This verification link is incomplete." };
  }

  try {
    await apiRequest("/doi/verify", {
      method: "POST",
      json: { member_id: memberId, code },
    });
    return { ok: true, message: "Your email address is verified." };
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message };
    return { ok: false, error: "Something went wrong. Please try again." };
  }
}
