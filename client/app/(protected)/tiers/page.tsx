"use client";

import { createTier } from "@/lib/actions";
import { useMemberStats, useTiers } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { CardGridSkeleton } from "@/components/ui/Skeletons";
import { LayersIcon, PlusIcon } from "@/components/ui/icons";
import { TierCard } from "@/components/tiers/TierCard";
import { TierFields } from "@/components/tiers/TierFields";

/** A tier change alters the member distribution too, so refresh both. */
function useTierRevalidate() {
  const revalidate = useRevalidate();
  return () => {
    revalidate.tiers();
    revalidate.members();
  };
}

function NewTierButton() {
  const onChange = useTierRevalidate();
  return (
    <FormDialog
      trigger={
        <Button>
          <PlusIcon /> New tier
        </Button>
      }
      title="New tier"
      description="Members reaching the point threshold earn at this multiplier."
      action={createTier}
      submitLabel="Create tier"
      onSuccess={onChange}
    >
      <TierFields />
    </FormDialog>
  );
}

export default function TiersPage() {
  const { data: tiers } = useTiers();
  const { data: stats } = useMemberStats();
  const onChange = useTierRevalidate();

  const countFor = (tierId: string) => stats?.by_tier[tierId] ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tiers"
        description="Point thresholds that apply an earn-rate multiplier."
        actions={<NewTierButton />}
      />

      {tiers === undefined ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <CardGridSkeleton count={3} />
        </div>
      ) : tiers.length === 0 ? (
        <Card>
          <EmptyState
            icon={<LayersIcon />}
            title="No tiers yet"
            description="Create tiers to reward members with higher earn rates as their balance grows."
            action={<NewTierButton />}
          />
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tiers.map((tier) => (
            <TierCard
              key={tier.id}
              tier={tier}
              count={stats ? countFor(tier.id) : undefined}
              onChange={onChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}
