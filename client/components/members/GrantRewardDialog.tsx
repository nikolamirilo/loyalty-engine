"use client";

import { useState } from "react";

import { assignPrize, redeemReward } from "@/lib/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import { formatNumber } from "@/lib/format";
import type { Reward } from "@/lib/types";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { GiftIcon } from "@/components/ui/icons";

export function GrantRewardDialog({
  memberId,
  rewards,
  balance,
}: {
  memberId: string;
  rewards: Reward[];
  balance: number;
}) {
  const [open, setOpen] = useState(false);
  const revalidate = useRevalidate();
  const onMutated = () => {
    revalidate.members();
    revalidate.rewards();
  };
  const available = rewards.filter(
    (r) => r.is_active && !(r.stock != null && r.stock <= 0),
  );

  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)}>
        <GiftIcon /> Redeem / assign
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Rewards"
        description="Redeem a reward for points, or assign one as a free prize."
        size="lg"
      >
        {available.length === 0 ? (
          <EmptyState
            icon={<GiftIcon />}
            title="No available rewards"
            description="Create an active, in-stock reward first."
          />
        ) : (
          <ul className="max-h-[60vh] divide-y divide-line overflow-y-auto">
            {available.map((reward) => {
              const affordable = balance >= reward.points_cost;
              return (
                <li key={reward.id} className="flex items-center gap-3 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-foreground">
                      {reward.name}
                    </p>
                    <p className="text-xs text-muted">
                      {formatNumber(reward.points_cost)} pts
                      {reward.stock != null && ` · ${reward.stock} left`}
                    </p>
                  </div>
                  <ActionButton
                    size="sm"
                    variant="secondary"
                    action={assignPrize.bind(null, memberId, reward.id)}
                    successMessage="Prize assigned."
                    onDone={onMutated}
                  >
                    Assign free
                  </ActionButton>
                  <ActionButton
                    size="sm"
                    action={redeemReward.bind(null, memberId, reward.id)}
                    successMessage="Reward redeemed."
                    onDone={onMutated}
                    disabled={!affordable}
                    title={
                      affordable
                        ? undefined
                        : "Insufficient points to redeem"
                    }
                  >
                    Redeem
                  </ActionButton>
                </li>
              );
            })}
          </ul>
        )}
      </Dialog>
    </>
  );
}
