"use server";

import type { ActionState } from "@/lib/action-state";
import { ApiError, apiRequest } from "@/lib/api";

/**
 * Server Action behind the public /p/[slug]/claim page, opened from a prize
 * email.
 *
 * Like /verify, the member is not signed in, so the call can't go through the
 * session-gated /api/le proxy and runs here with the bearer token kept on the
 * server. The token is the only input, and the API alone decides which prize
 * and program it names, so no program is sent (`programId: null`).
 */
export async function claimPrizeWithLink(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const token = String(fd.get("token") ?? "").trim();
  if (!token) return { ok: false, error: "This prize link is incomplete." };

  try {
    await apiRequest("/prizes/claim", {
      method: "POST",
      json: { token },
      programId: null,
    });
    return { ok: true, message: "Your prize is claimed." };
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message };
    console.error("[action] unexpected error:", e);
    return { ok: false, error: "Something went wrong. Please try again." };
  }
}
