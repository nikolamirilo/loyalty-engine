"use server";

import { timingSafeEqual } from "node:crypto";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import type { ActionState } from "@/lib/action-state";
import { ADMIN_PASSWORD, ADMIN_USERNAME, LOCKOUT_MS } from "./config";
import { clearAttempts, lockRemainingMs, registerFailure } from "./attempts";
import { createSession, destroySession } from "./session";

const LOCKOUT_MINUTES = Math.round(LOCKOUT_MS / 60_000);

/** Best-effort client IP from proxy headers; a single bucket in local dev. */
async function clientIp(): Promise<string> {
  const h = await headers();
  const forwarded = h.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0].trim();
  return h.get("x-real-ip")?.trim() || "unknown";
}

/** Constant-time compare that doesn't reveal length via an early return. */
function safeEqual(a: string, b: string): boolean {
  const left = Buffer.from(a, "utf8");
  const right = Buffer.from(b, "utf8");
  if (left.length !== right.length) {
    timingSafeEqual(left, left); // keep timing comparable, then fail
    return false;
  }
  return timingSafeEqual(left, right);
}

function lockoutMessage(remainingMs: number): string {
  const minutes = Math.max(1, Math.ceil(remainingMs / 60_000));
  return `Too many failed attempts. Try again in ${minutes} minute${
    minutes === 1 ? "" : "s"
  }.`;
}

export async function login(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const username = String(formData.get("username") ?? "");
  const password = String(formData.get("password") ?? "");
  const ip = await clientIp();

  const remaining = lockRemainingMs(ip);
  if (remaining > 0) {
    return { ok: false, error: lockoutMessage(remaining) };
  }

  // Evaluate both comparisons up front so neither is short-circuited away.
  const usernameOk = safeEqual(username, ADMIN_USERNAME);
  const passwordOk = safeEqual(password, ADMIN_PASSWORD);

  if (usernameOk && passwordOk) {
    clearAttempts(ip);
    await createSession();
    redirect("/"); // throws NEXT_REDIRECT — keep outside any try/catch
  }

  const result = registerFailure(ip);
  if (result.locked) {
    return { ok: false, error: lockoutMessage(result.remainingMs) };
  }

  const left = result.attemptsLeft;
  return {
    ok: false,
    error: `Invalid username or password. ${left} attempt${
      left === 1 ? "" : "s"
    } left before a ${LOCKOUT_MINUTES}-minute lockout.`,
  };
}

export async function logout(): Promise<void> {
  await destroySession();
  redirect("/login");
}
