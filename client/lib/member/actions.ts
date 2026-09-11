"use server";

import { revalidatePath } from "next/cache";

import type { ActionState } from "@/lib/action-state";
import { ApiError, apiRequest } from "@/lib/api";
import { getSessionMemberId } from "@/lib/memberAuth/session";

/**
 * Self-service profile edits for the signed-in member.
 *
 * The member id is read from the session cookie and never from the form: a
 * hidden id field would let anyone PATCH any member through this action.
 */
export async function updateProfile(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const memberId = await getSessionMemberId();
  if (!memberId) {
    return { ok: false, error: "Your session has expired. Please sign in again." };
  }

  const name = String(fd.get("name") ?? "").trim();
  const email = String(fd.get("email") ?? "").trim();
  const phone = String(fd.get("phone") ?? "").trim();

  if (!name) return { ok: false, error: "Enter your name." };
  if (!email) return { ok: false, error: "Enter your email address." };

  try {
    await apiRequest(`/members/${memberId}`, {
      method: "PATCH",
      // Phone is sent as "" rather than null when cleared: the API builds its
      // update with `exclude_none`, so a null would be dropped and the old
      // number would stay on the record.
      json: { name, email, phone },
    });
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message };
    console.error("[action] unexpected error:", e);
    return { ok: false, error: "Something went wrong. Please try again." };
  }

  revalidatePath("/account");
  return { ok: true, message: "Profile updated." };
}

/**
 * Buy a product as the signed-in member.
 *
 * No real payment happens and no balance is checked - the member pays with
 * unlimited "credit card" funds - this only records a `Purchase` row so spend
 * and frequency can be tracked. The member id comes from the session cookie,
 * never from a form field, for the same reason as `updateProfile`.
 */
export async function purchaseProduct(productId: string): Promise<ActionState> {
  const memberId = await getSessionMemberId();
  if (!memberId) {
    return { ok: false, error: "Your session has expired. Please sign in again." };
  }

  try {
    await apiRequest(`/members/${memberId}/purchases`, {
      method: "POST",
      json: { productId, quantity: 1 },
    });
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message };
    console.error("[action] unexpected error:", e);
    return { ok: false, error: "Something went wrong. Please try again." };
  }

  revalidatePath("/products");
  return { ok: true, message: "Purchase complete." };
}
