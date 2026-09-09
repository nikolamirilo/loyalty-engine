import type { Metadata } from "next";
import Image from "next/image";
import { redirect } from "next/navigation";

import { getSessionMemberId } from "@/lib/memberAuth/session";
import { AuthForm } from "./AuthForm";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Sign in - Loyalty App",
};

export default async function LoginPage() {
  // The proxy already gates this route; this is defense-in-depth.
  if (await getSessionMemberId()) redirect("/home");

  return (
    <main className="flex min-h-dvh items-center justify-center bg-surface-2 px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <Image
            src="/logo.svg"
            alt="Loyalty App"
            width={48}
            height={48}
            className="h-12 w-12 shadow-sm"
            priority
          />
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              Loyalty App
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
