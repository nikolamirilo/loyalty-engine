import type { Metadata } from "next";
import Image from "next/image";
import { redirect } from "next/navigation";

import { isAuthenticated } from "@/lib/auth/session";
import { LoginForm } from "./LoginForm";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Sign in — Loyalty Engine",
};

export default async function LoginPage() {
  // The proxy already gates this route; this is defense-in-depth.
  if (await isAuthenticated()) redirect("/");

  return (
    <main className="flex min-h-dvh items-center justify-center bg-surface-2 px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <Image
            src="/logo.svg"
            alt="Loyalty Engine"
            width={48}
            height={48}
            className="h-12 w-12 shadow-sm"
            priority
          />
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              Loyalty Engine
            </h1>
            <p className="mt-0.5 text-sm text-muted">
              Sign in to the admin console
            </p>
          </div>
        </div>
        <div className="rounded-xl border border-line bg-surface p-6 shadow-sm">
          <LoginForm />
        </div>
      </div>
    </main>
  );
}
