import { createTier, deleteTier } from "@/lib/actions";
import { getMembers, getTiers } from "@/lib/api";
import { formatNumber, tierForBalance } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Field, Input } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { LayersIcon, PlusIcon, TrashIcon } from "@/components/ui/icons";

function NewTierButton() {
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
    >
      <Field label="Name" htmlFor="tier-name">
        <Input id="tier-name" name="name" placeholder="e.g. Gold" required />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Min points" htmlFor="tier-min" hint="≥ 0">
          <Input
            id="tier-min"
            name="min_points"
            type="number"
            min={0}
            step={1}
            defaultValue={0}
            required
          />
        </Field>
        <Field label="Multiplier" htmlFor="tier-mult" hint="> 0">
          <Input
            id="tier-mult"
            name="multiplier"
            type="number"
            min={0}
            step="0.1"
            defaultValue={1}
            required
          />
        </Field>
      </div>
    </FormDialog>
  );
}

export default async function TiersPage() {
  const [tiers, members] = await Promise.all([getTiers(), getMembers()]);

  const counts = new Map<string, number>();
  for (const member of members) {
    const tier = tierForBalance(tiers, member.pointsBalance);
    if (tier) counts.set(tier.id, (counts.get(tier.id) ?? 0) + 1);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tiers"
        description="Point thresholds that apply an earn-rate multiplier."
        actions={<NewTierButton />}
      />

      {tiers.length === 0 ? (
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
            <Card key={tier.id} className="flex flex-col p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-yellow/15 text-xl text-accent-yellow">
                    <LayersIcon />
                  </span>
                  <div>
                    <p className="font-semibold text-foreground">{tier.name}</p>
                    <p className="text-xs text-faint">
                      {counts.get(tier.id) ?? 0} member
                      {(counts.get(tier.id) ?? 0) === 1 ? "" : "s"}
                    </p>
                  </div>
                </div>
                <ConfirmButton
                  trigger={
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Delete ${tier.name}`}
                      className="text-danger"
                    >
                      <TrashIcon />
                    </Button>
                  }
                  title={`Delete "${tier.name}"?`}
                  description="Members in this tier will fall back to the next-lowest tier. This cannot be undone."
                  confirmLabel="Delete tier"
                  action={deleteTier.bind(null, tier.id)}
                  successMessage="Tier deleted."
                />
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-surface-2 px-3 py-2.5">
                  <p className="text-xs text-muted">From</p>
                  <p className="mt-0.5 font-semibold text-foreground tabular-nums">
                    {formatNumber(tier.min_points)}
                    <span className="ml-1 text-xs font-normal text-faint">
                      pts
                    </span>
                  </p>
                </div>
                <div className="rounded-lg bg-surface-2 px-3 py-2.5">
                  <p className="text-xs text-muted">Earn rate</p>
                  <p className="mt-0.5 font-semibold text-foreground tabular-nums">
                    {tier.multiplier}×
                  </p>
                </div>
              </div>
              <div className="mt-3">
                <Badge tone="primary">×{tier.multiplier} points on earn</Badge>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
