import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { getBalance, getPrizes } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { getSessionMemberId } from "@/lib/memberAuth/session";
import { claimMyPrize } from "@/lib/member/actions";
import { memberProgramId } from "@/lib/server/program";
import { ActionButton } from "@/components/ui/ActionButton";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatTile } from "@/components/ui/StatTile";
import { BalanceAutoRefresh } from "@/components/wallet/BalanceAutoRefresh";
import { CoinsIcon, GiftIcon, WalletIcon } from "@/components/ui/icons";

export const metadata: Metadata = { title: "Wallet - Loyalty App" };
export const dynamic = "force-dynamic";

export default async function WalletPage() {
  // The proxy and MemberLayout already gate this route; this is defense-in-depth.
  const memberId = await getSessionMemberId();
  if (!memberId) redirect("/login");

  const programId = await memberProgramId();
  const [balance, prizes] = await Promise.all([
    getBalance(memberId, programId),
    // "assigned" prizes are the ones granted to the member that they haven't
    // paid points for ("redeemed" is the other `RedemptionSource`). Each is
    // unclaimed until the member claims it here or from the prize email.
    getPrizes(memberId, "assigned", programId),
  ]);

  return (
    <div className="space-y-6">
      <BalanceAutoRefresh />
      <PageHeader title="Wallet" description="Your points and the prizes you've won." />

      <StatTile
        label="Points balance"
        value={balance.pointsBalance}
        icon={<CoinsIcon />}
        accent="yellow"
      />

      <Card>
        <CardHeader
          title="Prizes"
          description="Prizes you've won. Claim them here or from your email."
        />
        {prizes.length === 0 ? (
          <EmptyState
            icon={<WalletIcon />}
            title="Nothing here yet"
            description="Prizes you win will show up here."
          />
        ) : (
          <ul className="divide-y divide-line">
            {prizes.map((prize) => (
              <li
                key={prize.id}
                className="flex items-center gap-3 px-5 py-4"
              >
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-orange/12 text-lg text-accent-orange">
                  <GiftIcon />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-foreground">
                    {prize.reward.name}
                  </p>
                  <p className="text-xs text-faint">{formatDateTime(prize.createdAt)}</p>
                </div>
                {prize.claimedAt ? (
                  <Badge tone="success">Claimed</Badge>
                ) : (
                  <ActionButton size="sm" action={claimMyPrize.bind(null, prize.id)}>
                    Claim
                  </ActionButton>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
