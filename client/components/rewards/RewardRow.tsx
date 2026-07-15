"use client";

import { deleteReward, setRewardActive, updateReward } from "@/lib/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import { formatNumber } from "@/lib/format";
import type { Reward } from "@/lib/types";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/Button";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { FormDialog } from "@/components/ui/FormDialog";
import { ActiveBadge } from "@/components/ui/StatusBadge";
import { TD, TR } from "@/components/ui/Table";
import { BanIcon, CheckIcon, PencilIcon, TrashIcon } from "@/components/ui/icons";
import { RewardFields } from "./RewardFields";

function EditRewardButton({ reward }: { reward: Reward }) {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <Button variant="ghost" size="icon" aria-label={`Edit ${reward.name}`}>
          <PencilIcon />
        </Button>
      }
      title="Edit reward"
      action={updateReward}
      submitLabel="Save changes"
      onSuccess={() => revalidate.rewards()}
    >
      <input type="hidden" name="id" value={reward.id} />
      <RewardFields reward={reward} />
    </FormDialog>
  );
}

export function RewardRow({ reward }: { reward: Reward }) {
  const revalidate = useRevalidate();
  const outOfStock = reward.stock != null && reward.stock <= 0;
  return (
    <TR className="hover:bg-surface-2/60">
      <TD>
        <div className="font-medium text-foreground">{reward.name}</div>
        {reward.description && (
          <div className="mt-0.5 line-clamp-1 max-w-md text-xs text-muted">
            {reward.description}
          </div>
        )}
      </TD>
      <TD className="text-right font-medium tabular-nums whitespace-nowrap">
        {formatNumber(reward.points_cost)}
        <span className="ml-1 text-xs font-normal text-faint">pts</span>
      </TD>
      <TD className="text-right tabular-nums whitespace-nowrap">
        {reward.stock == null ? (
          <span className="text-faint">Unlimited</span>
        ) : outOfStock ? (
          <span className="text-danger-fg">Out of stock</span>
        ) : (
          formatNumber(reward.stock)
        )}
      </TD>
      <TD>
        <ActiveBadge active={reward.is_active} />
      </TD>
      <TD>
        <div className="flex items-center justify-end gap-1">
          <ActionButton
            variant="ghost"
            size="sm"
            action={setRewardActive.bind(null, reward.id, !reward.is_active)}
            successMessage={reward.is_active ? "Reward deactivated." : "Reward activated."}
            onDone={() => revalidate.rewards()}
          >
            {reward.is_active ? (
              <>
                <BanIcon /> Deactivate
              </>
            ) : (
              <>
                <CheckIcon /> Activate
              </>
            )}
          </ActionButton>
          <EditRewardButton reward={reward} />
          <ConfirmButton
            trigger={
              <Button
                variant="ghost"
                size="icon"
                aria-label={`Delete ${reward.name}`}
                className="text-danger"
              >
                <TrashIcon />
              </Button>
            }
            title={`Delete "${reward.name}"?`}
            description="This removes the reward from the catalog. Existing redemption history is kept."
            confirmLabel="Delete reward"
            action={deleteReward.bind(null, reward.id)}
            successMessage="Reward deleted."
            onSuccess={() => revalidate.rewards()}
          />
        </div>
      </TD>
    </TR>
  );
}
