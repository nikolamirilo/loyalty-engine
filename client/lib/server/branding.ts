import "server-only";

import { getPrograms } from "@/lib/api";
import { activeProgramId, memberProgramId } from "@/lib/server/program";
import type { Program } from "@/lib/types";

/**
 * Which program's branding a page should wear — SERVER ONLY.
 *
 * Each surface resolves it the same way it resolves the data it shows (see
 * lib/server/program.ts), so the logo and colours on screen always belong to
 * the dataset on screen.
 */

/** `selected` among `programs`, falling back to the one the API would use. */
export function resolveProgram(programs: Program[], selected: string | undefined): Program | null {
  if (selected) {
    const match = programs.find((p) => p.slug === selected || p.id === selected);
    if (match) return match;
  }
  // The selection names a program that no longer exists (someone deleted it,
  // or this is a first visit), so fall back to the same one the API would.
  return programs.find((p) => p.isDefault) ?? programs[0] ?? null;
}

/**
 * Branding is decoration: a failure to load it must never take the page down,
 * so the stock look is what an unreachable API gets.
 */
async function programsOrEmpty(): Promise<Program[]> {
  return getPrograms().catch(() => [] as Program[]);
}

/** Every program, and the one the console is pointed at. */
export async function consolePrograms(): Promise<{ programs: Program[]; current: Program | null }> {
  const [programs, selected] = await Promise.all([programsOrEmpty(), activeProgramId()]);
  return { programs, current: resolveProgram(programs, selected) };
}

/** The program the member app is showing: the signed-in member's, else the
 *  one the login page would authenticate against. */
export async function memberBrandProgram(): Promise<Program | null> {
  const [programs, selected] = await Promise.all([programsOrEmpty(), memberProgramId()]);
  return resolveProgram(programs, selected);
}
