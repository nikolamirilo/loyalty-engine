"use client";

import {
  assignChallengeToSegment,
  deleteChallenge,
  updateChallenge,
} from "@/lib/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import { formatDate, formatNumber } from "@/lib/format";
import type { Challenge, Reward } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { Field, Input } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { ActiveBadge } from "@/components/ui/StatusBadge";
import {
  AwardIcon,
  ClockIcon,
  CoinsIcon,
  PencilIcon,
  TargetIcon,
  TrashIcon,
  UsersIcon,
} from "@/components/ui/icons";
import { ChallengeFields } from "./ChallengeFields";

export function ChallengeCard({
  challenge,
  rewards,
}: {
  challenge: Challenge;
  rewards: Reward[];
}) {
  const revalidate = useRevalidate();
  const prize = challenge.reward_id
    ? rewards.find((r) => r.id === challenge.reward_id)
    : null;

  return (
    <Card className="flex flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent-aqua/15 text-xl text-accent-aqua">
            <TargetIcon />
          </span>
          <div className="min-w-0">
            <p className="font-semibold text-foreground">{challenge.name}</p>
            {challenge.description && (
              <p className="mt-0.5 line-clamp-2 text-[13px] text-muted">
                {challenge.description}
              </p>
            )}
          </div>
        </div>
        <ActiveBadge active={challenge.is_active} />
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Badge tone="neutral">
          <TargetIcon className="text-[13px]" /> Target {formatNumber(challenge.target_value)}
        </Badge>
        {challenge.reward_points > 0 && (
          <Badge tone="primary">
            <CoinsIcon className="text-[13px]" /> {formatNumber(challenge.reward_points)} pts
          </Badge>
        )}
        {prize && (
          <Badge tone="warning">
            <AwardIcon className="text-[13px]" /> {prize.name}
          </Badge>
        )}
        {challenge.expires_at && (
          <Badge tone="neutral">
            <ClockIcon className="text-[13px]" /> Expires {formatDate(challenge.expires_at)}
          </Badge>
        )}
      </div>

      <div className="mt-5 flex items-center gap-1 border-t border-line pt-4">
        <AssignSegmentButton challenge={challenge} />
        <div className="ml-auto flex items-center gap-1">
          <FormDialog
            trigger={
              <Button
                variant="ghost"
                size="icon"
                aria-label={`Edit ${challenge.name}`}
              >
                <PencilIcon />
              </Button>
            }
            title="Edit challenge"
            action={updateChallenge}
            submitLabel="Save changes"
            onSuccess={() => revalidate.challenges()}
          >
            <input type="hidden" name="id" value={challenge.id} />
            <ChallengeFields challenge={challenge} rewards={rewards} />
          </FormDialog>
          <ConfirmButton
            trigger={
              <Button
                variant="ghost"
                size="icon"
                aria-label={`Delete ${challenge.name}`}
                className="text-danger"
              >
                <TrashIcon />
              </Button>
            }
            title={`Delete "${challenge.name}"?`}
            description="This removes the challenge and all of its member assignments. This cannot be undone."
            confirmLabel="Delete challenge"
            action={deleteChallenge.bind(null, challenge.id)}
            successMessage="Challenge deleted."
            onSuccess={() => revalidate.challenges()}
          />
        </div>
      </div>
    </Card>
  );
}

function AssignSegmentButton({ challenge }: { challenge: Challenge }) {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <Button variant="secondary" size="sm">
          <UsersIcon /> Assign to segment
        </Button>
      }
      title="Assign to segment"
      description={`Assign "${challenge.name}" to every member in a segment.`}
      action={assignChallengeToSegment}
      submitLabel="Assign"
      onSuccess={() => {
        revalidate.challenges();
        revalidate.members();
      }}
    >
      <input type="hidden" name="challenge_id" value={challenge.id} />
      <Field
        label="Segment"
        htmlFor="segment"
        help="Members whose segments include this value will be assigned."
      >
        <Input id="segment" name="segment" placeholder="e.g. vip" required />
      </Field>
    </FormDialog>
  );
}
