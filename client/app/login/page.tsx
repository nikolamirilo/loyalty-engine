import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { BrandLogo } from "@/components/branding/BrandLogo";
import { ProgramTheme } from "@/components/branding/ProgramTheme";
import { cn } from "@/lib/format";
import { getSessionMemberId } from "@/lib/memberAuth/session";
import { memberBrandProgram } from "@/lib/server/branding";
import { AuthForm } from "./AuthForm";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Sign in - Loyalty App",
};

export default async function LoginPage() {
  // The proxy already gates this route; this is defense-in-depth.
  if (await getSessionMemberId()) redirect("/home");

  // Signing in always lands in the default program, so that is the brand on
  // the door (no session here, so memberBrandProgram resolves to it).
  const program = await memberBrandProgram();

  return (
    <main className="flex min-h-dvh items-center justify-center bg-surface-2 px-4 py-10">
      <ProgramTheme program={program} />
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <BrandLogo
            src={program?.logoUrl}
            alt={program?.name ?? "Loyalty App"}
            className={cn("h-12 max-w-40", !program?.logoUrl && "shadow-sm")}
          />
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              {program?.name ?? "Loyalty App"}
            </h1>
            <p className="mt-0.5 text-sm text-muted">
              Log in or create an account to continue
            </p>
          </div>
        </div>
        <div className="rounded-xl border border-line bg-surface p-6 shadow-sm">
          <AuthForm />
        </div>
      </div>
    </main>
  );
}
