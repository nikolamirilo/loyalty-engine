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
    <Button
      variant="secondary"
      size="sm"
      onClick={copyId}
      className="w-full justify-center sm:w-auto"
    >
      <CopyIcon /> Copy ID
    </Button>
  );
}
