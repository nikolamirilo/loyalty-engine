"use client";

import { deleteTier, updateTier } from "@/lib/actions";
import { formatNumber } from "@/lib/format";
import type { Tier } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { FormDialog } from "@/components/ui/FormDialog";
import { LayersIcon, PencilIcon, TrashIcon } from "@/components/ui/icons";
import { TierFields } from "./TierFields";

export function TierCard({
  tier,
  count,
  onChange,
}: {
  tier: Tier;
  count: number | undefined;
  onChange: () => void;
}) {
  return (
    <Card className="flex flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-yellow/15 text-xl text-accent-yellow">
            <LayersIcon />
          </span>
          <div>
            <p className="font-semibold text-foreground">{tier.name}</p>
            <p className="text-xs text-faint">
              {count === undefined ? "…" : `${count} member${count === 1 ? "" : "s"}`}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <FormDialog
            trigger={
              <Button variant="ghost" size="icon" aria-label={`Edit ${tier.name}`}>
                <PencilIcon />
              </Button>
            }
            title="Edit tier"
            description="Members reaching the point threshold earn at this multiplier."
            action={updateTier}
            submitLabel="Save changes"
            onSuccess={onChange}
          >
            <input type="hidden" name="id" value={tier.id} />
            <TierFields tier={tier} />
          </FormDialog>
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
            onSuccess={onChange}
          />
        </div>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-surface-2 px-3 py-2.5">
          <p className="text-xs text-muted">From</p>
          <p className="mt-0.5 font-semibold text-foreground tabular-nums">
            {formatNumber(tier.minPoints)}
            <span className="ml-1 text-xs font-normal text-faint">pts</span>
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
  );
}
