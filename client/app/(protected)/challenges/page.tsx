"use client";

import { createChallenge } from "@/lib/actions";
import { useChallenges, useRewards } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { Reward } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { CardGridSkeleton } from "@/components/ui/Skeletons";
import { ChallengeCard } from "@/components/challenges/ChallengeCard";
import { ChallengeFields } from "@/components/challenges/ChallengeFields";
import { PlusIcon, TargetIcon } from "@/components/ui/icons";

function NewChallengeButton({ rewards }: { rewards: Reward[] }) {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <Button>
          <PlusIcon /> New challenge
        </Button>
      }
      title="New challenge"
      description="Define a goal members can complete to earn points or a prize."
      action={createChallenge}
      submitLabel="Create challenge"
      onSuccess={() => revalidate.challenges()}
    >
      <ChallengeFields rewards={rewards} />
    </FormDialog>
  );
}

export default function ChallengesPage() {
  const { data: challenges } = useChallenges();
  const { data: rewards } = useRewards();
  const activeCount = challenges?.filter((c) => c.is_active).length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Challenges"
        description={
          challenges && challenges.length
            ? `${challenges.length} challenge${challenges.length === 1 ? "" : "s"} · ${activeCount} active`
            : "Goals members complete to earn points and prizes."
        }
        actions={<NewChallengeButton rewards={rewards ?? []} />}
      />

      {challenges === undefined ? (
        <div className="grid gap-4 md:grid-cols-2">
          <CardGridSkeleton count={4} />
        </div>
      ) : challenges.length === 0 ? (
        <Card>
          <EmptyState
            icon={<TargetIcon />}
            title="No challenges yet"
            description="Create a challenge to give members a goal - completing it grants points and/or a prize."
            action={<NewChallengeButton rewards={rewards ?? []} />}
          />
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {challenges.map((challenge) => (
            <ChallengeCard
              key={challenge.id}
              challenge={challenge}
              rewards={rewards ?? []}
            />
          ))}
        </div>
      )}
    </div>
  );
}
