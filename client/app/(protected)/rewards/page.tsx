"use client";

import { createReward } from "@/lib/actions";
import { useRewards } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { TableRowsSkeleton } from "@/components/ui/Skeletons";
import { RewardFields } from "@/components/rewards/RewardFields";
import { RewardRow } from "@/components/rewards/RewardRow";
import { Table, TBody, TH, THead, TR } from "@/components/ui/Table";
import { GiftIcon, PlusIcon } from "@/components/ui/icons";

function NewRewardButton() {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <Button>
          <PlusIcon /> New reward
        </Button>
      }
      title="New reward"
      description="Add a redeemable reward to the catalog."
      action={createReward}
      submitLabel="Create reward"
      onSuccess={() => revalidate.rewards()}
    >
      <RewardFields />
    </FormDialog>
  );
}

export default function RewardsPage() {
  const { data: rewards } = useRewards();
  const activeCount = rewards?.filter((r) => r.is_active).length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Rewards"
        description={
          rewards && rewards.length
            ? `${rewards.length} reward${rewards.length === 1 ? "" : "s"} · ${activeCount} active`
            : "Catalog of redeemable rewards."
        }
        actions={<NewRewardButton />}
      />

      <Card>
        {rewards === undefined ? (
          <TableRowsSkeleton />
        ) : rewards.length === 0 ? (
          <EmptyState
            icon={<GiftIcon />}
            title="No rewards yet"
            description="Create your first reward so members have something to redeem their points for."
            action={<NewRewardButton />}
          />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Reward</TH>
                <TH className="text-right">Cost</TH>
                <TH className="text-right">Stock</TH>
                <TH>Status</TH>
                <TH className="text-right">Actions</TH>
              </TR>
            </THead>
            <TBody>
              {rewards.map((reward) => (
                <RewardRow key={reward.id} reward={reward} />
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
