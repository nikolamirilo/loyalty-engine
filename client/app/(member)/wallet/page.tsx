import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { getBalance, getPrizes } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { getSessionMemberId } from "@/lib/memberAuth/session";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatTile } from "@/components/ui/StatTile";
import { CoinsIcon, GiftIcon, WalletIcon } from "@/components/ui/icons";

export const metadata: Metadata = { title: "Wallet - Loyalty App" };
export const dynamic = "force-dynamic";

export default async function WalletPage() {
  // The proxy and MemberLayout already gate this route; this is defense-in-depth.
  const memberId = await getSessionMemberId();
  if (!memberId) redirect("/login");

  const [balance, prizes] = await Promise.all([
    getBalance(memberId),
    // "assigned" prizes are the ones granted to the member that they haven't
    // paid points for ("redeemed" is the other `RedemptionSource`) - i.e. the
    // products they have that aren't redeemed yet.
    getPrizes(memberId, "assigned"),
  ]);

  return (
    <div className="space-y-6">
      <PageHeader title="Wallet" description="Your points and unredeemed products." />

      <StatTile
        label="Points balance"
        value={balance.pointsBalance}
        icon={<CoinsIcon />}
        accent="yellow"
      />

      <Card>
        <CardHeader
          title="Rewards"
          description="Rewards you have that aren't redeemed yet."
        />
        {prizes.length === 0 ? (
          <EmptyState
            icon={<WalletIcon />}
            title="Nothing here yet"
            description="Unredeemed products you're given will show up here."
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
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">
                    {prize.reward.name}
                  </p>
                  <p className="text-xs text-faint">{formatDateTime(prize.createdAt)}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
