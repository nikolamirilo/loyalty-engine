"use client";

import { useTransition } from "react";

import { deleteReward, setRewardActive, updateReward } from "@/lib/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import { formatNumber } from "@/lib/format";
import type { Reward } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { DropdownMenu, DropdownMenuItem } from "@/components/ui/DropdownMenu";
import { FormDialog } from "@/components/ui/FormDialog";
import { ActiveBadge } from "@/components/ui/StatusBadge";
import { TD, TR } from "@/components/ui/Table";
import { useToast } from "@/components/ui/Toast";
import {
  BanIcon,
  CheckIcon,
  CopyIcon,
  MoreVerticalIcon,
  PencilIcon,
  TrashIcon,
} from "@/components/ui/icons";
import { RewardFields } from "./RewardFields";

function EditRewardMenuItem({ reward }: { reward: Reward }) {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <DropdownMenuItem>
          <PencilIcon /> Edit
        </DropdownMenuItem>
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
  const toast = useToast();
  const [togglePending, startToggle] = useTransition();
  const outOfStock = reward.stock != null && reward.stock <= 0;

  const copyId = async () => {
    try {
      await navigator.clipboard.writeText(reward.id);
      toast.success("Reward ID copied.");
    } catch {
      toast.error("Couldn't copy reward ID.");
    }
  };

  const toggleActive = () => {
    startToggle(async () => {
      const res = await setRewardActive(reward.id, !reward.isActive);
      if (res.ok) {
        toast.success(reward.isActive ? "Reward deactivated." : "Reward activated.");
        revalidate.rewards();
      } else {
        toast.error(res.error ?? "Something went wrong.");
      }
    });
  };

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
        {formatNumber(reward.pointsCost)}
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
        <ActiveBadge active={reward.isActive} />
      </TD>
      <TD>
        <div className="flex justify-end">
          <DropdownMenu
            trigger={
              <Button variant="ghost" size="icon" aria-label={`Actions for ${reward.name}`}>
                <MoreVerticalIcon />
              </Button>
            }
          >
            <DropdownMenuItem onClick={toggleActive} disabled={togglePending}>
              {reward.isActive ? (
                <>
                  <BanIcon /> Deactivate
                </>
              ) : (
                <>
                  <CheckIcon /> Activate
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={copyId}>
              <CopyIcon /> Copy ID
            </DropdownMenuItem>
            <EditRewardMenuItem reward={reward} />
            <ConfirmButton
              trigger={
                <DropdownMenuItem danger>
                  <TrashIcon /> Delete
                </DropdownMenuItem>
              }
              title={`Delete "${reward.name}"?`}
              description="This removes the reward from the catalog. Existing redemption history is kept."
              confirmLabel="Delete reward"
              action={deleteReward.bind(null, reward.id)}
              successMessage="Reward deleted."
              onSuccess={() => revalidate.rewards()}
            />
          </DropdownMenu>
        </div>
      </TD>
    </TR>
  );
}
