import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/layout/AppShell";
import { ProgramSwitcher } from "@/components/layout/ProgramSwitcher";
import { getPrograms } from "@/lib/api";
import { isAuthenticated } from "@/lib/auth/session";
import { activeProgramId } from "@/lib/server/program";
import type { Program } from "@/lib/types";
import { Providers } from "./providers";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Loyalty Engine - Admin",
  description:
    "Admin console for the Loyalty Engine: members, points, rewards, challenges, and tiers.",
};

/** The program the console is pointed at, or null if the API had none to give. */
function resolveCurrent(programs: Program[], selected: string | undefined): Program | null {
  if (selected) {
    const match = programs.find((p) => p.slug === selected || p.id === selected);
    if (match) return match;
  }
  // The cookie names a program that no longer exists (someone deleted it, or
  // this is a first visit), so fall back to the same one the API would.
  return programs.find((p) => p.isDefault) ?? programs[0] ?? null;
}

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // The proxy is the primary gate; this re-check guards the initial render and
  // keeps the console protected even if the proxy matcher ever changes.
  if (!(await isAuthenticated())) redirect("/admin/login");

  // A failure here must not blank the console: the pages below surface their
  // own errors, and an empty switcher still leaves the API's default program
  // answering every request.
  const programs = await getPrograms().catch(() => [] as Program[]);
  const current = resolveCurrent(programs, await activeProgramId());

  return (
    <Providers programId={current?.slug ?? "default"}>
      <AppShell
        programSwitcher={
          <ProgramSwitcher programs={programs} currentSlug={current?.slug ?? ""} />
        }
      >
        {children}
      </AppShell>
    </Providers>
  );
}
