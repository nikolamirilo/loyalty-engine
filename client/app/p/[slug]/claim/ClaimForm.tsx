"use client";

import { useActionState } from "react";

import { idleState } from "@/lib/action-state";
import { claimPrizeWithLink } from "@/lib/prizes/actions";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { SubmitButton } from "@/components/ui/SubmitButton";
import { CheckCircleIcon } from "@/components/ui/icons";

/**
 * The one thing the prize link asks of a member: press a button. The token
 * comes from the emailed link and rides along as a hidden input.
 */
export function ClaimForm({ token }: { token: string }) {
  const [state, formAction] = useActionState(claimPrizeWithLink, idleState);

  if (state.ok) {
    return (
      <div className="flex flex-col items-center gap-2 text-center">
        <CheckCircleIcon className="text-3xl text-success" />
        <p className="text-sm font-medium text-foreground">
          {state.message ?? "Your prize is claimed."}
        </p>
        <p className="text-[0.8125rem] text-muted">You can close this page.</p>
      </div>
    );
  }

  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="token" value={token} />
      {state.error && <ErrorBanner message={state.error} />}
      <SubmitButton className="w-full">Claim my prize</SubmitButton>
    </form>
  );
}
