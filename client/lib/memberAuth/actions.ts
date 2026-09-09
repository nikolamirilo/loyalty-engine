"use server";

import { redirect } from "next/navigation";

import type { ActionState } from "@/lib/action-state";
import { ApiError, apiRequest } from "@/lib/api";
import type { Member } from "@/lib/types";
import { createMemberSession, destroySession } from "./session";

/**
 * The member email/signup/login-code flow. Runs before any session exists,
 * so - like the DOI actions in `lib/doi/actions.ts` - these call the API
 * directly rather than through the session-gated `/api/le` proxy.
 */

export async function requestLoginCode(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const email = String(fd.get("email") ?? "").trim();
  if (!email) return { ok: false, error: "Enter your email address." };

  try {
    await apiRequest("/auth/login", { method: "POST", json: { email } });
    return { ok: true };
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message };
    return { ok: false, error: "Something went wrong. Please try again." };
  }
}

export async function requestSignupCode(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const email = String(fd.get("email") ?? "").trim();
  const name = String(fd.get("name") ?? "").trim();
  const phone = String(fd.get("phone") ?? "").trim();
  if (!email || !name) {
    return { ok: false, error: "Enter your name and email address." };
  }

  try {
    await apiRequest("/auth/signup", {
      method: "POST",
      json: { email, name, phone: phone || undefined },
    });
    return { ok: true };
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message };
    return { ok: false, error: "Something went wrong. Please try again." };
  }
}

/**
 * Verifies the code and, on success, signs the member in and redirects to
 * the tab shell. `email` rides along as a hidden field set by `AuthForm` -
 * the member never re-types it for this step.
 */
export async function verifyLoginCode(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const email = String(fd.get("email") ?? "").trim();
  const code = String(fd.get("code") ?? "").trim();
  if (!email || !code) {
    return { ok: false, error: "Enter the code from your email." };
  }

  let member: Member;
  try {
    const result = await apiRequest<{ member: Member }>("/auth/verify", {
      method: "POST",
      json: { email, code },
    });
    member = result.member;
  } catch (e) {
    if (e instanceof ApiError) return { ok: false, error: e.message };
    return { ok: false, error: "Something went wrong. Please try again." };
  }

  await createMemberSession(member.id);
  redirect("/home"); // throws NEXT_REDIRECT - keep outside any try/catch
}

export async function memberLogout(): Promise<void> {
  await destroySession();
  redirect("/");
}
