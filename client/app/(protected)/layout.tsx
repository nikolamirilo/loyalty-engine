import { redirect } from "next/navigation";

import { AppShell } from "@/components/layout/AppShell";
import { isAuthenticated } from "@/lib/auth/session";
import { Providers } from "./providers";

export const dynamic = "force-dynamic";

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // The proxy is the primary gate; this re-check guards the initial render and
  // keeps the console protected even if the proxy matcher ever changes.
  if (!(await isAuthenticated())) redirect("/login");

  return (
    <Providers>
      <AppShell>{children}</AppShell>
    </Providers>
  );
}
