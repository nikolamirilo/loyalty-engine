import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { ProgramTheme } from "@/components/branding/ProgramTheme";
import { AppShell } from "@/components/layout/AppShell";
import { ProgramSwitcher } from "@/components/layout/ProgramSwitcher";
import { isAuthenticated } from "@/lib/auth/session";
import { consolePrograms } from "@/lib/server/branding";
import { Providers } from "./providers";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Loyalty Engine - Admin",
  description:
    "Admin console for the Loyalty Engine: members, points, rewards, challenges, and tiers.",
};

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
  const { programs, current } = await consolePrograms();

  return (
    <Providers programId={current?.slug ?? "default"}>
      {/* The console wears the selected program's colours and logo, so a demo
          of a brand's program looks like that brand from the first screen. */}
      <ProgramTheme program={current} />
      <AppShell
        program={current}
        programSwitcher={
          <ProgramSwitcher programs={programs} currentSlug={current?.slug ?? ""} />
        }
      >
        {children}
      </AppShell>
    </Providers>
  );
}
