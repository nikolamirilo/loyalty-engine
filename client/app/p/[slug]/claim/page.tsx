import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { BrandLogo } from "@/components/branding/BrandLogo";
import { ProgramTheme } from "@/components/branding/ProgramTheme";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { CheckCircleIcon, GiftIcon } from "@/components/ui/icons";
import { ApiError, getPrizeClaim, getPrograms } from "@/lib/api";
import { cn, formatDate } from "@/lib/format";
import { resolveProgram } from "@/lib/server/branding";
import type { PrizeClaim, Program } from "@/lib/types";
import { ClaimForm } from "./ClaimForm";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Claim your prize - Loyalty App",
  // A claim link is member-specific; keep it out of search.
  robots: { index: false, follow: false },
};

/** First value only: `?token=a&token=b` must not become "a,b". */
function param(value: string | string[] | undefined): string {
  return (Array.isArray(value) ? value[0] : value)?.trim() ?? "";
}

async function loadClaim(token: string): Promise<{ claim: PrizeClaim | null; error: string | null }> {
  if (!token) {
    return { claim: null, error: "This prize link is incomplete. Open the link from your email again." };
  }
  try {
    return { claim: await getPrizeClaim(token), error: null };
  } catch (e) {
    if (e instanceof ApiError) return { claim: null, error: e.message };
    console.error("[claim] unexpected error:", e);
    return { claim: null, error: "Something went wrong. Please try again." };
  }
}

/**
 * Public landing page for the prize email's "Claim your prize" button.
 *
 * The email links here as `/p/<programSlug>/claim?token=<token>`. The token
 * alone names the prize, and the API reads the prize's program from it; the
 * slug is only there so the page wears the right brand. If the two disagree
 * (an edited or outdated link) the page redirects to the prize's real program.
 * Like /verify, it needs no session: the member presses one button.
 */
export default async function ClaimPrizePage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ slug }, query] = await Promise.all([params, searchParams]);
  const token = param(query.token);
  const { claim, error } = await loadClaim(token);

  if (claim && claim.program.slug !== slug) {
    redirect(`/p/${encodeURIComponent(claim.program.slug)}/claim?token=${encodeURIComponent(token)}`);
  }

  // Without a valid claim there is no program from the token, so the slug
  // picks the brand (falling back to the default program).
  const program: Program | null =
    claim?.program ?? resolveProgram(await getPrograms().catch(() => []), slug);

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
              {claim ? `Congratulations, ${claim.memberName}!` : "Claim your prize"}
            </h1>
            {program && <p className="mt-0.5 text-sm text-muted">{program.name}</p>}
          </div>
        </div>
        <div className="rounded-xl border border-line bg-surface p-6 shadow-sm">
          {claim ? (
            <div className="space-y-5">
              <div className="flex flex-col items-center gap-2 text-center">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-subtle text-2xl text-primary-subtle-fg">
                  <GiftIcon />
                </span>
                <p className="text-base font-semibold text-foreground">{claim.reward.name}</p>
                {claim.reward.description && (
                  <p className="text-sm text-muted">{claim.reward.description}</p>
                )}
              </div>
              {claim.claimedAt ? (
                <div className="flex flex-col items-center gap-2 text-center">
                  <CheckCircleIcon className="text-3xl text-success" />
                  <p className="text-sm font-medium text-foreground">
                    You claimed this prize on {formatDate(claim.claimedAt)}.
                  </p>
                </div>
              ) : claim.expired ? (
                <div className="space-y-3 text-center">
                  <ErrorBanner message="This link has expired, but your prize is still waiting in your wallet." />
                  <Link href="/login" className="text-sm font-medium text-primary hover:underline">
                    Sign in to claim it
                  </Link>
                </div>
              ) : (
                <ClaimForm token={token} />
              )}
            </div>
          ) : (
            <ErrorBanner message={error ?? "This prize link is not valid."} />
          )}
        </div>
      </div>
    </main>
  );
}
