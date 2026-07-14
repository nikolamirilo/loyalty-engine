import Link from "next/link";

import { getChallenges, getMembers, getRewards, getTiers } from "@/lib/api";
import {
  compactNumber,
  formatNumber,
  memberTier,
  tierForBalance,
} from "@/lib/format";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProgressMeter } from "@/components/ui/ProgressMeter";
import { StatTile } from "@/components/ui/StatTile";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import {
  ChevronRightIcon,
  CoinsIcon,
  GiftIcon,
  LayersIcon,
  TargetIcon,
  UsersIcon,
} from "@/components/ui/icons";

export default async function DashboardPage() {
  const [members, tiers, rewards, challenges] = await Promise.all([
    getMembers(),
    getTiers(),
    getRewards(),
    getChallenges(),
  ]);

  const pointsInCirculation = members.reduce((sum, m) => sum + m.pointsBalance, 0);
  const activeRewards = rewards.filter((r) => r.is_active).length;
  const activeChallenges = challenges.filter((c) => c.is_active).length;

  // Members per tier (highest tier first), plus an untiered bucket.
  const perTier = tiers.map((tier) => ({
    id: tier.id,
    name: tier.name,
    count: members.filter((m) => tierForBalance(tiers, m.pointsBalance)?.id === tier.id)
      .length,
  }));
  const untiered = members.filter(
    (m) => tierForBalance(tiers, m.pointsBalance) === null,
  ).length;
  const distribution = [...perTier].reverse();
  if (untiered > 0 || tiers.length === 0) {
    distribution.push({ id: "none", name: "No tier", count: untiered });
  }

  const recentMembers = members.slice(0, 6);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your loyalty program."
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Members"
          value={members.length}
          icon={<UsersIcon />}
          accent="blue"
        />
        <StatTile
          label="Points in circulation"
          value={pointsInCirculation}
          icon={<CoinsIcon />}
          accent="aqua"
        />
        <StatTile
          label="Active rewards"
          value={activeRewards}
          sub={`${rewards.length} total`}
          icon={<GiftIcon />}
          accent="orange"
        />
        <StatTile
          label="Active challenges"
          value={activeChallenges}
          sub={`${challenges.length} total`}
          icon={<TargetIcon />}
          accent="violet"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent members */}
        <Card className="overflow-hidden lg:col-span-2">
          <CardHeader
            title="Members"
            description="Most recent in the program"
            action={
              <Link
                href="/members"
                className="inline-flex items-center gap-0.5 text-sm font-medium text-primary hover:underline"
              >
                View all <ChevronRightIcon className="text-base" />
              </Link>
            }
          />
          {recentMembers.length === 0 ? (
            <EmptyState
              icon={<UsersIcon />}
              title="No members yet"
              description="Add your first member from the Members page."
            />
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Member</TH>
                  <TH>Tier</TH>
                  <TH className="text-right">Balance</TH>
                </TR>
              </THead>
              <TBody>
                {recentMembers.map((member) => {
                  const tier = memberTier(tiers, member);
                  return (
                    <TR key={member.id} className="group hover:bg-surface-2/60">
                      <TD>
                        <Link
                          href={`/members/${member.id}`}
                          className="flex items-center gap-3"
                        >
                          <Avatar name={member.name} />
                          <span className="min-w-0">
                            <span className="block truncate font-medium text-foreground group-hover:text-primary">
                              {member.name}
                            </span>
                            <span className="block truncate text-xs text-muted">
                              {member.email}
                            </span>
                          </span>
                        </Link>
                      </TD>
                      <TD>
                        {tier ? (
                          <Badge tone="primary">{tier.name}</Badge>
                        ) : (
                          <span className="text-xs text-faint">-</span>
                        )}
                      </TD>
                      <TD className="text-right font-semibold tabular-nums whitespace-nowrap">
                        {formatNumber(member.pointsBalance)}
                        <span className="ml-1 text-xs font-normal text-faint">
                          pts
                        </span>
                      </TD>
                    </TR>
                  );
                })}
              </TBody>
            </Table>
          )}
        </Card>

        {/* Tier distribution */}
        <Card>
          <CardHeader
            title="Tier distribution"
            description="Members by current tier"
          />
          <div className="space-y-4 p-5">
            {members.length === 0 || distribution.length === 0 ? (
              <EmptyState
                icon={<LayersIcon />}
                title="Nothing to show"
                description="Add members and tiers to see the breakdown."
                className="py-8"
              />
            ) : (
              distribution.map((row) => (
                <div key={row.id}>
                  <div className="mb-1.5 flex items-center justify-between text-sm">
                    <span className="font-medium text-foreground">
                      {row.name}
                    </span>
                    <span className="text-muted tabular-nums">
                      {row.count}
                      <span className="ml-1 text-xs text-faint">
                        {members.length > 0
                          ? `(${Math.round((row.count / members.length) * 100)}%)`
                          : ""}
                      </span>
                    </span>
                  </div>
                  <ProgressMeter value={row.count} max={members.length} />
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
