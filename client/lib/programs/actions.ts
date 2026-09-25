"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";

import type { ActionState } from "@/lib/action-state";
import { ApiError, apiRequest } from "@/lib/api";
import { PROGRAM_COOKIE } from "@/lib/server/program";
import { HEX_COLOR } from "@/lib/theme";
import type { Program } from "@/lib/types";

/**
 * Programs are the console's top-level switcher: each has its own rewards,
 * products, challenges, tiers, segments and member balances, and deleting one
 * takes all of that with it.
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

/** The API's own limit (api/app/services/program_branding.py), checked here
 * too so an oversized file fails with a clear message before it is sent. */
const MAX_LOGO_BYTES = 2 * 1024 * 1024;

interface Branding {
  primaryColor: string | null;
  secondaryColor: string | null;
  /** A newly chosen file, or null to leave the logo as it is. */
  logo: File | null;
  removeLogo: boolean;
}

/** "#0050AA", "0050aa" -> "#0050aa"; blank -> null (the stock colour). */
function readColor(fd: FormData, key: string): string | null | undefined {
  const raw = String(fd.get(key) ?? "").trim();
  if (!raw) return null;
  const hex = (raw.startsWith("#") ? raw : `#${raw}`).toLowerCase();
  return HEX_COLOR.test(hex) ? hex : undefined;
}

/** The branding fields of ProgramFields, or the message for the first bad one. */
function readBranding(fd: FormData): Branding | { error: string } {
  const primaryColor = readColor(fd, "primaryColor");
  const secondaryColor = readColor(fd, "secondaryColor");
  if (primaryColor === undefined) return { error: "Enter the primary colour as a hex code, like #0050aa." };
  if (secondaryColor === undefined) return { error: "Enter the secondary colour as a hex code, like #fff000." };

  const file = fd.get("logo");
  const logo = file instanceof File && file.size > 0 ? file : null;
  if (logo && logo.size > MAX_LOGO_BYTES) return { error: "The logo must be 2 MB or smaller." };

  return { primaryColor, secondaryColor, logo, removeLogo: fd.get("removeLogo") === "on" };
}

/** Upload the new logo, or remove the old one, as the form asked. */
async function applyLogo(programId: string, branding: Branding): Promise<void> {
  if (branding.logo) {
    await apiRequest<Program>(`/programs/${programId}/logo`, {
      method: "PUT",
      file: branding.logo,
      programId: null,
    });
  } else if (branding.removeLogo) {
    await apiRequest<Program>(`/programs/${programId}/logo`, {
      method: "DELETE",
      programId: null,
    });
  }
}

export async function createProgram(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const name = String(fd.get("name") ?? "").trim();
  const description = String(fd.get("description") ?? "").trim();
  if (!name) return { ok: false, error: "Enter a name." };
  const branding = readBranding(fd);
  if ("error" in branding) return { ok: false, error: branding.error };

  let program: Program;
  try {
    // No slug: the API derives one from the name.
    program = await apiRequest<Program>("/programs", {
      method: "POST",
      json: {
        name,
        description: description || null,
        primaryColor: branding.primaryColor,
        secondaryColor: branding.secondaryColor,
      },
      programId: null,
    });
  } catch (e) {
    return fail(e);
  }

  try {
    await applyLogo(program.id, branding);
  } catch (e) {
    // The program exists now, so keeping the dialog open for a retry would
    // create a second one. Close it and say where to finish the job.
    refreshConsole();
    const reason = e instanceof ApiError ? e.message : "Something went wrong.";
    return { ok: true, message: `Program created, but the logo was not saved: ${reason} Add it with Edit.` };
  }
  refreshConsole();
  return { ok: true, message: "Program created." };
}

export async function updateProgram(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = String(fd.get("id") ?? "").trim();
  const name = String(fd.get("name") ?? "").trim();
  const description = String(fd.get("description") ?? "").trim();
  const isDefault = fd.get("isDefault") === "on";
  if (!id) return { ok: false, error: "No program selected." };
  if (!name) return { ok: false, error: "Enter a name." };
  const branding = readBranding(fd);
  if ("error" in branding) return { ok: false, error: branding.error };

  try {
    // The slug is left out, so it survives a rename - and so does the program
    // cookie, which holds it. A null colour resets it to the stock theme.
    await apiRequest<Program>(`/programs/${id}`, {
      method: "PATCH",
      json: {
        name,
        description: description || null,
        isDefault,
        primaryColor: branding.primaryColor,
        secondaryColor: branding.secondaryColor,
      },
      programId: null,
    });
    await applyLogo(id, branding);

    refreshConsole();
    return { ok: true, message: "Program updated." };
  } catch (e) {
    // The fields may have saved before the logo failed; show what did.
    refreshConsole();
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
