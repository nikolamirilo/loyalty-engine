"use server";

import { revalidatePath } from "next/cache";

import type { ActionState } from "@/lib/action-state";
import { ApiError, apiRequest } from "@/lib/api";
import { createMemberSession, getSessionMemberId } from "@/lib/memberAuth/session";
import { memberProgramId } from "@/lib/server/program";
import type { Member } from "@/lib/types";

/**
 * Switching the program a member is looking at.
 *
 * A member id is per program: the same person holds a separate membership,
 * with its own points and tier, in each one. So switching is not just a
 * cookie change - it swaps the signed-in member id for the one that belongs
 * to the target program, joining it first if they never had one.
 */
export async function switchMemberProgram(programId: string): Promise<ActionState> {
  const memberId = await getSessionMemberId();
  if (!memberId) return { ok: false, error: "You are not signed in." };
  if (!programId) return { ok: false, error: "No program selected." };

  try {
    // Resolved in the program the session is currently in, which is what
    // proves the caller is this person before handing back their membership
    // somewhere else.
    const membership = await apiRequest<Member>(
      `/members/${memberId}/programs/${programId}`,
      { method: "POST", programId: await memberProgramId() },
    );

    // The session carries the program, so this one write moves both: the old
    // member id does not exist in the new program, and leaving the two out of
    // step would 404 every page.
    await createMemberSession(membership.id, membership.programId);

    revalidatePath("/", "layout");
    return { ok: true, message: "Switched program." };
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message };
    console.error("[action] unexpected error:", e);
    return { ok: false, error: "Something went wrong. Please try again." };
  }
}
