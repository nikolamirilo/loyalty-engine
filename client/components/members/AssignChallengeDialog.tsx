"use client";

import { useState } from "react";

import { assignChallengeToMember } from "@/lib/actions";
import { formatNumber } from "@/lib/format";
import type { Challenge } from "@/lib/types";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { PlusIcon, TargetIcon } from "@/components/ui/icons";

export function AssignChallengeDialog({
  memberId,
  challenges,
  assignedIds,
}: {
  memberId: string;
  challenges: Challenge[];
  assignedIds: string[];
}) {
  const [open, setOpen] = useState(false);
  const available = challenges.filter(
    (c) => c.is_active && !assignedIds.includes(c.id),
  );

  return (
    <>
      <Button size="sm" variant="secondary" onClick={() => setOpen(true)}>
        <PlusIcon /> Assign challenge
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Assign a challenge"
        description="Active challenges the member hasn't been assigned yet."
        size="lg"
      >
        {available.length === 0 ? (
          <EmptyState
            icon={<TargetIcon />}
            title="Nothing to assign"
            description="This member already has every active challenge, or none are active."
          />
        ) : (
          <ul className="max-h-[60vh] divide-y divide-line overflow-y-auto">
            {available.map((challenge) => (
              <li key={challenge.id} className="flex items-center gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-foreground">
                    {challenge.name}
                  </p>
                  <p className="text-xs text-muted">
                    Target {formatNumber(challenge.target_value)}
                    {challenge.reward_points > 0 &&
                      ` · ${formatNumber(challenge.reward_points)} pts`}
                  </p>
                </div>
                <ActionButton
                  size="sm"
                  action={assignChallengeToMember.bind(
                    null,
                    memberId,
                    challenge.id,
                  )}
                  successMessage="Challenge assigned."
                >
                  Assign
                </ActionButton>
              </li>
            ))}
          </ul>
        )}
      </Dialog>
    </>
  );
}
