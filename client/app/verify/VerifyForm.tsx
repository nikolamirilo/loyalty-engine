"use client";

import { useActionState } from "react";

import { idleState } from "@/lib/action-state";
import { verifyMemberEmail } from "@/lib/doi/actions";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { SubmitButton } from "@/components/ui/SubmitButton";
import { CheckCircleIcon } from "@/components/ui/icons";

/**
 * The one thing the DOI link flow asks of a member: press a button.
 *
 * The id and code come from the emailed link and ride along as hidden inputs -
 * nothing to read, type, or copy.
 */
export function VerifyForm({
  memberId,
  code,
}: {
  memberId: string;
  code: string;
}) {
  const [state, formAction] = useActionState(verifyMemberEmail, idleState);

  if (state.ok) {
    return (
      <div className="flex flex-col items-center gap-3 text-center">
        <CheckCircleIcon className="text-3xl text-success" />
        <p className="text-sm font-medium text-foreground">
          {state.message ?? "Your email address is verified."}
        </p>
        <p className="text-[13px] text-muted">You can close this page.</p>
      </div>
    );
  }

  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="memberId" value={memberId} />
      <input type="hidden" name="code" value={code} />
      <p className="text-center text-sm text-muted">
        Press the button below to confirm this email address.
      </p>
      {state.error && <ErrorBanner message={state.error} />}
      <SubmitButton className="w-full">Verify my email</SubmitButton>
    </form>
  );
}
