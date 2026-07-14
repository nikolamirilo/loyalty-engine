"use client";

import { useTransition } from "react";

import type { ActionState } from "@/lib/action-state";
import { Button, type ButtonProps } from "./Button";
import { useToast } from "./Toast";

/**
 * A button that runs a Server Action on click (no confirmation), surfacing the
 * result as a toast. For destructive actions use `ConfirmButton` instead.
 */
export function ActionButton({
  action,
  successMessage,
  onDone,
  children,
  ...props
}: Omit<ButtonProps, "onClick" | "loading"> & {
  action: () => Promise<ActionState>;
  successMessage?: string;
  onDone?: () => void;
}) {
  const [pending, startTransition] = useTransition();
  const toast = useToast();

  return (
    <Button
      loading={pending}
      onClick={() =>
        startTransition(async () => {
          const res = await action();
          if (res.ok) {
            toast.success(successMessage ?? res.message ?? "Done.");
            onDone?.();
          } else {
            toast.error(res.error ?? "Something went wrong.");
          }
        })
      }
      {...props}
    >
      {children}
    </Button>
  );
}
