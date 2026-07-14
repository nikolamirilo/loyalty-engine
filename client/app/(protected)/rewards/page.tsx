import { createReward } from "@/lib/actions";
import { getRewards } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { RewardFields } from "@/components/rewards/RewardFields";
import { RewardRow } from "@/components/rewards/RewardRow";
import { Table, TBody, TH, THead, TR } from "@/components/ui/Table";
import { GiftIcon, PlusIcon } from "@/components/ui/icons";

function NewRewardButton() {
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
    >
      <RewardFields />
    </FormDialog>
  );
}

export default async function RewardsPage() {
  const rewards = await getRewards();
  const activeCount = rewards.filter((r) => r.is_active).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Rewards"
        description={
          rewards.length
            ? `${rewards.length} reward${rewards.length === 1 ? "" : "s"} · ${activeCount} active`
            : "Catalog of redeemable rewards."
        }
        actions={<NewRewardButton />}
      />

      <Card>
        {rewards.length === 0 ? (
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
