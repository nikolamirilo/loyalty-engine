"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import type { ActionState } from "@/lib/action-state";
import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { ErrorBanner } from "./ErrorBanner";
import { useToast } from "./Toast";

/**
 * A trigger that opens a confirmation dialog and runs a Server Action on
 * confirm. Errors show inline in the dialog; success toasts and (optionally)
 * navigates away.
 */
export function ConfirmButton({
  trigger,
  title,
  description,
  confirmLabel = "Confirm",
  action,
  danger = true,
  redirectTo,
  successMessage,
  onSuccess,
}: {
  trigger: React.ReactElement<{ onClick?: () => void }>;
  title: string;
  description?: string;
  confirmLabel?: string;
  action: () => Promise<ActionState>;
  danger?: boolean;
  redirectTo?: string;
  successMessage?: string;
  /** Called after the action succeeds — e.g. to revalidate SWR caches. */
  onSuccess?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const toast = useToast();
  const router = useRouter();

  const onConfirm = () => {
    setError(null);
    startTransition(async () => {
      const res = await action();
      if (res.ok) {
        toast.success(successMessage ?? res.message ?? "Done.");
        onSuccess?.();
        setOpen(false);
        if (redirectTo) router.push(redirectTo);
      } else {
        setError(res.error ?? "Something went wrong.");
      }
    });
  };

  return (
    <>
      {/* Wrap rather than cloneElement - see FormDialog for why: cloning a
          trigger built in a Server Component drops nested component types
          (icons) to `undefined` during dev SSR. */}
      <span className="contents" onClick={() => setOpen(true)}>
        {trigger}
      </span>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={title}
        description={description}
        size="sm"
      >
        <div className="space-y-4">
          {error && <ErrorBanner message={error} />}
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant={danger ? "danger" : "primary"}
              loading={pending}
              onClick={onConfirm}
            >
              {confirmLabel}
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}
