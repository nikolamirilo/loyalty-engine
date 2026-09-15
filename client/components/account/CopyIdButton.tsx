"use client";

import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { CopyIcon } from "@/components/ui/icons";

/** Copies the signed-in member's id to the clipboard. Same pattern as the
 * admin console's member/reward/challenge "Copy ID" buttons. */
export function CopyIdButton({ id }: { id: string }) {
  const toast = useToast();

  const copyId = async () => {
    try {
      await navigator.clipboard.writeText(id);
      toast.success("User ID copied.");
    } catch {
      toast.error("Couldn't copy user ID.");
    }
  };

  return (
    // Icon-only, matching the edit button it sits beside. The label lives in
    // `aria-label`/`title` rather than on screen: the id is a support handle a
    // member copies when asked for it, so it does not need to announce itself
    // next to the name it belongs to. Same shape as the admin console's
    // icon-only row actions.
    <Button
      variant="secondary"
      size="icon"
      onClick={copyId}
      aria-label="Copy member ID"
      title="Copy member ID"
      className="shrink-0"
    >
      <CopyIcon />
    </Button>
  );
}
