"use client";

import Link from "next/link";

import {
  useChallenges,
  useMemberStats,
  useMembers,
  useRewards,
  useTiers,
} from "@/lib/swr/hooks";
import { formatNumber, memberTier } from "@/lib/format";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProgressMeter } from "@/components/ui/ProgressMeter";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatTile } from "@/components/ui/StatTile";
import { StatTileSkeleton, TableRowsSkeleton } from "@/components/ui/Skeletons";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import {
  ChevronRightIcon,
  CoinsIcon,
  GiftIcon,
  LayersIcon,
  TargetIcon,
  UsersIcon,
} from "@/components/ui/icons";

export default function DashboardPage() {
  const { data: stats } = useMemberStats();
  const { data: tiers } = useTiers();
  const { data: rewards } = useRewards();
  const { data: challenges } = useChallenges();
  const { data: recentMembers } = useMembers({ limit: 6 });

  const activeRewards = rewards?.filter((r) => r.is_active).length ?? 0;
  const activeChallenges = challenges?.filter((c) => c.is_active).length ?? 0;

  // Members per tier (highest first), plus an untiered bucket.
  const distribution =
    stats && tiers
      ? (() => {
          const perTier = tiers.map((tier) => ({
            id: tier.id,
            name: tier.name,
            count: stats.by_tier[tier.id] ?? 0,
          }));
          const rows = [...perTier].reverse();
          if (stats.untiered > 0 || tiers.length === 0) {
            rows.push({ id: "none", name: "No tier", count: stats.untiered });
          }
          return rows;
        })()
      : null;

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description="Overview of your loyalty program." />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats ? (
          <StatTile label="Members" value={stats.count} icon={<UsersIcon />} accent="blue" />
        ) : (
          <StatTileSkeleton />
        )}
        {stats ? (
          <StatTile
            label="Points in circulation"
            value={stats.points_in_circulation}
            icon={<CoinsIcon />}
            accent="aqua"
          />
        ) : (
          <StatTileSkeleton />
        )}
        {rewards ? (
          <StatTile
            label="Active rewards"
            value={activeRewards}
            sub={`${rewards.length} total`}
            icon={<GiftIcon />}
            accent="orange"
          />
        ) : (
          <StatTileSkeleton />
        )}
        {challenges ? (
          <StatTile
            label="Active challenges"
            value={activeChallenges}
            sub={`${challenges.length} total`}
            icon={<TargetIcon />}
            accent="violet"
          />
        ) : (
          <StatTileSkeleton />
        )}
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
          {recentMembers === undefined ? (
            <TableRowsSkeleton rows={6} />
          ) : recentMembers.length === 0 ? (
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
                  const tier = tiers ? memberTier(tiers, member) : null;
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
                        <span className="ml-1 text-xs font-normal text-faint">pts</span>
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
          <CardHeader title="Tier distribution" description="Members by current tier" />
          <div className="space-y-4 p-5">
            {distribution === null ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-1.5">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-2 w-full rounded-full" />
                </div>
              ))
            ) : stats && stats.count === 0 ? (
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
                    <span className="font-medium text-foreground">{row.name}</span>
                    <span className="text-muted tabular-nums">
                      {row.count}
                      <span className="ml-1 text-xs text-faint">
                        {stats && stats.count > 0
                          ? `(${Math.round((row.count / stats.count) * 100)}%)`
                          : ""}
                      </span>
                    </span>
                  </div>
                  <ProgressMeter value={row.count} max={stats?.count ?? 0} />
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
