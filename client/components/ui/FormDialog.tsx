"use client";

import { useActionState, useEffect, useState } from "react";

import { idleState, type ActionState } from "@/lib/action-state";
import { Button } from "./Button";
import { Dialog } from "./Dialog";
import { ErrorBanner } from "./ErrorBanner";
import { SubmitButton } from "./SubmitButton";
import { useToast } from "./Toast";

type FormAction = (prev: ActionState, fd: FormData) => Promise<ActionState>;

/**
 * A dialog wrapping a `<form>` bound to a Server Action via `useActionState`.
 * The form body only mounts while the dialog is open, so `defaultValue`s and
 * action state reset cleanly on every open. On success it toasts and closes.
 */
export function FormDialog({
  trigger,
  title,
  description,
  action,
  submitLabel = "Save",
  size = "md",
  children,
}: {
  trigger: React.ReactElement<{ onClick?: () => void }>;
  title: string;
  description?: string;
  action: FormAction;
  submitLabel?: string;
  size?: "sm" | "md" | "lg";
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Wrap rather than cloneElement: the trigger is built in a Server
          Component and passed across the client boundary, and cloning an
          element whose subtree contains components (e.g. an icon) resolves
          those nested types to `undefined` during dev SSR. A display:contents
          wrapper adds no box and lets the click bubble up to open the dialog. */}
      <span className="contents" onClick={() => setOpen(true)}>
        {trigger}
      </span>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={title}
        description={description}
        size={size}
      >
        <FormBody
          action={action}
          submitLabel={submitLabel}
          onDone={() => setOpen(false)}
        >
          {children}
        </FormBody>
      </Dialog>
    </>
  );
}

function FormBody({
  action,
  submitLabel,
  onDone,
  children,
}: {
  action: FormAction;
  submitLabel: string;
  onDone: () => void;
  children: React.ReactNode;
}) {
  const [state, formAction] = useActionState(action, idleState);
  const toast = useToast();

  useEffect(() => {
    if (state.ok) {
      toast.success(state.message ?? "Saved.");
      onDone();
    }
    // Only react to a change in the action's result.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  return (
    <form action={formAction} className="space-y-4">
      <div className="space-y-4">{children}</div>
      {state.error && <ErrorBanner message={state.error} />}
      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="secondary" onClick={onDone}>
          Cancel
        </Button>
        <SubmitButton>{submitLabel}</SubmitButton>
      </div>
    </form>
  );
}
