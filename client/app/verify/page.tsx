import type { Metadata } from "next";
import Image from "next/image";

import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { VerifyForm } from "./VerifyForm";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Verify your email - Loyalty Engine",
  // A verification link is single-use and member-specific; keep it out of search.
  robots: { index: false, follow: false },
};

/** First value only: `?code=a&code=b` must not become "a,b". */
function param(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value)?.trim() ?? "";
}

/**
 * Public landing page for the DOI `type: "link"` email.
 *
 * The email links here as `/verify?memberId=<id>&code=<code>`; the member
 * presses one button and the Server Action posts the pair to the API. It is
 * deliberately outside `(protected)` and exempted in `proxy.ts` - a member
 * confirming their address has no admin session and never will.
 */
export default async function VerifyPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const memberId = param(params.memberId);
  const code = param(params.code);
  const linkComplete = memberId !== "" && code !== "";

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
              Verify your email
            </h1>
            <p className="mt-0.5 text-sm text-muted">
              One tap and you&apos;re done
            </p>
          </div>
        </div>
        <div className="rounded-xl border border-line bg-surface p-6 shadow-sm">
          {linkComplete ? (
            <VerifyForm memberId={memberId} code={code} />
          ) : (
            <ErrorBanner message="This verification link is incomplete. Open the link from your email again, or request a new one." />
          )}
        </div>
      </div>
    </main>
  );
}
