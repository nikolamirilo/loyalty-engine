"use client";

import {
  addChallengeProgress,
  completeChallenge,
  unassignChallenge,
} from "@/lib/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import { formatNumber } from "@/lib/format";
import type { ChallengeAssignment } from "@/lib/types";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/Button";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { Field, Input } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { ProgressMeter } from "@/components/ui/ProgressMeter";
import { ChallengeStatusBadge } from "@/components/ui/StatusBadge";
import { CheckIcon, PlusIcon, TrashIcon } from "@/components/ui/icons";

export function MemberChallengeItem({
  assignment,
  memberId,
}: {
  assignment: ChallengeAssignment;
  memberId: string;
}) {
  const revalidate = useRevalidate();
  const challenge = assignment.challenge;
  const status = assignment.status;
  const isClosed = status === "completed" || status === "cancelled";
  const canProgress = status === "assigned" || status === "in_progress";
  const tone =
    status === "completed"
      ? "success"
      : status === "expired"
        ? "warning"
        : "primary";

  return (
    <div className="rounded-lg border border-line p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-medium text-foreground">{challenge.name}</p>
          {challenge.reward_points > 0 && (
            <p className="mt-0.5 text-xs text-muted">
              {formatNumber(challenge.reward_points)} pts on completion
            </p>
          )}
        </div>
        <ChallengeStatusBadge status={status} />
      </div>

      <div className="mt-3">
        <div className="mb-1.5 flex justify-between text-xs text-muted tabular-nums">
          <span>Progress</span>
          <span>
            {formatNumber(assignment.current_value)} /{" "}
            {formatNumber(challenge.target_value)}
          </span>
        </div>
        <ProgressMeter
          value={assignment.current_value}
          max={challenge.target_value}
          tone={tone}
        />
      </div>

      <div className="mt-3 flex items-center gap-1">
        {canProgress && (
          <FormDialog
            trigger={
              <Button size="sm" variant="secondary">
                <PlusIcon /> Progress
              </Button>
            }
            title="Add progress"
            description={`Record progress toward "${challenge.name}".`}
            action={addChallengeProgress}
            submitLabel="Add progress"
            onSuccess={() => revalidate.members()}
          >
            <input type="hidden" name="member_id" value={memberId} />
            <input type="hidden" name="challenge_id" value={challenge.id} />
            <Field label="Amount" htmlFor="progress-amount">
              <Input
                id="progress-amount"
                name="amount"
                type="number"
                min={1}
                step={1}
                defaultValue={1}
                required
                autoFocus
              />
            </Field>
            <Field label="Note" htmlFor="progress-desc" hint="optional">
              <Input id="progress-desc" name="description" placeholder="Optional" />
            </Field>
          </FormDialog>
        )}
        {!isClosed && (
          <ActionButton
            size="sm"
            variant="secondary"
            action={completeChallenge.bind(null, memberId, challenge.id)}
            successMessage="Challenge completed."
            onDone={() => revalidate.members()}
          >
            <CheckIcon /> Complete
          </ActionButton>
        )}
        <ConfirmButton
          trigger={
            <Button
              variant="ghost"
              size="icon"
              aria-label="Remove challenge"
              className="ml-auto text-danger"
            >
              <TrashIcon />
            </Button>
          }
          title={`Remove "${challenge.name}"?`}
          description="This unassigns the challenge from this member."
          confirmLabel="Remove"
          action={unassignChallenge.bind(null, memberId, challenge.id)}
          successMessage="Challenge removed."
          onSuccess={() => revalidate.members()}
        />
      </div>
    </div>
  );
}
