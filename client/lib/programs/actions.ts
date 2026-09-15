"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";

import type { ActionState } from "@/lib/action-state";
import { ApiError, apiRequest } from "@/lib/api";
import { PROGRAM_COOKIE } from "@/lib/server/program";
import type { Program } from "@/lib/types";

/**
 * Programs are the console's dataset switcher: creating one gives a demo its
 * own rewards, products, challenges, tiers, segments and members, and deleting
 * one takes all of that with it.
 *
 * These calls are deliberately unscoped (`programId: null`): /programs is the
 * one part of the API that is not inside a program.
 */

function fail(error: unknown): ActionState {
  if (error instanceof ApiError) return { ok: false, error: error.message };
  console.error("[action] unexpected error:", error);
  return { ok: false, error: "Something went wrong. Please try again." };
}

/** Everything under /admin reads program-scoped data, so refresh the layout. */
function refreshConsole(): void {
  revalidatePath("/admin", "layout");
}

async function setProgramCookie(slug: string): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(PROGRAM_COOKIE, slug, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
  });
}

export async function switchProgram(fd: FormData): Promise<void> {
  const slug = String(fd.get("slug") ?? "").trim();
  if (!slug) return;

  await setProgramCookie(slug);
  refreshConsole();
}

/**
 * Point a fresh session at the API's default program.
 *
 * Without this the console would send no `X-Program-Id` at all until someone
 * touched the switcher, leaving the API to fall back to its default on every
 * request: the same data, but chosen by the server rather than stated by the
 * console, and a warning logged each time. Called on login, where a Server
 * Action may set cookies (a Server Component may not).
 *
 * Failing here is not worth blocking a login for: the fallback still applies.
 */
export async function selectDefaultProgram(): Promise<void> {
  try {
    const programs = await apiRequest<Program[]>("/programs", { programId: null });
    const target = programs.find((p) => p.isDefault) ?? programs[0];
    if (target) await setProgramCookie(target.slug);
  } catch (e) {
    console.error("[action] could not preselect a program:", e);
  }
}

export async function clearProgramSelection(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(PROGRAM_COOKIE);
}

export async function createProgram(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const name = String(fd.get("name") ?? "").trim();
  const slug = String(fd.get("slug") ?? "").trim();
  const description = String(fd.get("description") ?? "").trim();
  if (!name || !slug) {
    return { ok: false, error: "Enter a name and a slug." };
  }

  try {
    await apiRequest<Program>("/programs", {
      method: "POST",
      json: { name, slug, description: description || null },
      programId: null,
    });
    refreshConsole();
    return { ok: true };
  } catch (e) {
    return fail(e);
  }
}

export async function removeProgram(id: string): Promise<ActionState> {
  if (!id) return { ok: false, error: "No program selected." };

  try {
    // Read it before deleting: afterwards there is no way to tell whether the
    // cookie was pointing at this one.
    const doomed = await apiRequest<Program>(`/programs/${id}`, { programId: null });
    await apiRequest(`/programs/${id}`, { method: "DELETE", programId: null });

    // A cookie naming a program that no longer exists would 404 every scoped
    // request until the admin happened to use the switcher.
    const selected = (await cookies()).get(PROGRAM_COOKIE)?.value;
    if (selected === doomed.slug || selected === doomed.id) {
      await selectDefaultProgram();
    }

    refreshConsole();
    return { ok: true, message: "Program deleted." };
  } catch (e) {
    return fail(e);
  }
}
