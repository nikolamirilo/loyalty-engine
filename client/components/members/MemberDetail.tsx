"use client";

import Link from "next/link";
import dynamic from "next/dynamic";

import {
  useChallenges,
  useMember,
  useMemberChallenges,
  useRedemptions,
  useRewards,
  useTiers,
  useTransactions,
} from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import { ApiError } from "@/lib/swr/error";
import { cn, formatDateTime, formatNumber, memberTier, signedNumber } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatTile } from "@/components/ui/StatTile";
import { TransactionBadge } from "@/components/ui/StatusBadge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { MemberChallengeItem } from "@/components/members/MemberChallengeItem";
import { MemberProfileCard } from "@/components/members/MemberProfileCard";
import {
  ChevronRightIcon,
  CoinsIcon,
  GiftIcon,
  TargetIcon,
  UsersIcon,
} from "@/components/ui/icons";

// Interaction-only dialog — lazy-loaded so its chunk (and the challenge list
// inside) isn't in the initial member-detail bundle.
const AssignChallengeDialog = dynamic(
  () =>
    import("@/components/members/AssignChallengeDialog").then(
      (m) => m.AssignChallengeDialog,
    ),
  { ssr: false },
);

/**
 * Member detail, rendered entirely client-side so navigation is instant: the
 * shell paints immediately and each section fills in as its own SWR hook
 * resolves, top-to-bottom by priority (profile → stats → activity →
 * redemptions → challenges). Nothing blocks the whole page on the slowest call.
 */
export function MemberDetail({ id }: { id: string }) {
  const revalidate = useRevalidate();
  const onMutated = () => revalidate.members();

  const { data: member, error: memberError } = useMember(id);
  const { data: tiers } = useTiers();
  const { data: transactions } = useTransactions(id);
  const { data: redemptions } = useRedemptions(id);
  const { data: memberChallenges } = useMemberChallenges(id);
  const { data: rewards } = useRewards(true);
  const { data: challenges } = useChallenges(true);

  if (memberError instanceof ApiError && memberError.status === 404) {
    return (
      <MessageState
        title="Member not found"
        description="This member may have been deleted."
      />
    );
  }
  if (memberError && !member) {
    return (
      <MessageState
        title="Couldn't load member"
        description={(memberError as Error)?.message ?? "Please try again."}
      />
    );
  }

  const tier = member && tiers ? memberTier(tiers, member) : null;
  const totalEarned = transactions
    ? transactions.filter((t) => t.type === "earn").reduce((s, t) => s + t.points, 0)
    : 0;
  const completedChallenges = memberChallenges
    ? memberChallenges.filter((c) => c.status === "completed").length
    : 0;
  const assignedIds = memberChallenges
    ? memberChallenges.map((c) => c.challengeId)
    : [];

  return (
    <div className="space-y-6">
      <Link
        href="/members"
        className="inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-foreground"
      >
        <ChevronRightIcon className="rotate-180 text-base" />
        All members
      </Link>

      {/* 1 — Profile: standard + custom fields, editable in place */}
      <MemberProfileCard
        member={member}
        tier={tier}
        tiersLoading={tiers === undefined}
        rewards={rewards ?? []}
        onMutated={onMutated}
      />

      {/* 2 — Stat tiles */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {member ? (
          <StatTile
            label="Points balance"
            value={member.pointsBalance}
            icon={<CoinsIcon />}
            accent="blue"
          />
        ) : (
          <StatTileSkeleton />
        )}
        {transactions ? (
          <StatTile
            label="Lifetime earned"
            value={totalEarned}
            icon={<CoinsIcon />}
            accent="aqua"
          />
        ) : (
          <StatTileSkeleton />
        )}
        {memberChallenges ? (
          <StatTile
            label="Challenges completed"
            value={`${completedChallenges}/${memberChallenges.length}`}
            icon={<TargetIcon />}
            accent="violet"
          />
        ) : (
          <StatTileSkeleton />
        )}
        {redemptions ? (
          <StatTile
            label="Redemptions"
            value={redemptions.length}
            icon={<GiftIcon />}
            accent="orange"
          />
        ) : (
          <StatTileSkeleton />
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: history */}
        <div className="space-y-6 lg:col-span-2">
          {/* 3 — Points activity */}
          <Card className="overflow-hidden">
            <CardHeader
              title="Points activity"
              description="Earn, burn, and adjustment history"
            />
            {transactions === undefined ? (
              <TableSkeleton />
            ) : transactions.length === 0 ? (
              <EmptyState
                icon={<CoinsIcon />}
                title="No activity yet"
                description="Points transactions will appear here."
              />
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Type</TH>
                    <TH className="text-right">Points</TH>
                    <TH>Description</TH>
                    <TH className="text-right">When</TH>
                  </TR>
                </THead>
                <TBody>
                  {transactions.map((t) => (
                    <TR key={t.id} className="hover:bg-surface-2/60">
                      <TD>
                        <TransactionBadge type={t.type} />
                      </TD>
                      <TD
                        className={cn(
                          "text-right font-semibold tabular-nums",
                          t.points > 0
                            ? "text-success-fg"
                            : t.points < 0
                              ? "text-danger-fg"
                              : "text-muted",
                        )}
                      >
                        {signedNumber(t.points)}
                      </TD>
                      <TD className="max-w-xs truncate text-muted">
                        {t.description ?? "-"}
                      </TD>
                      <TD className="text-right whitespace-nowrap text-muted">
                        {formatDateTime(t.createdAt)}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </Card>

          {/* 4 — Redemptions */}
          <Card className="overflow-hidden">
            <CardHeader
              title="Redemptions & prizes"
              description="Rewards redeemed for points or assigned for free"
            />
            {redemptions === undefined ? (
              <TableSkeleton />
            ) : redemptions.length === 0 ? (
              <EmptyState
                icon={<GiftIcon />}
                title="No redemptions yet"
                description="Redeemed rewards and assigned prizes will appear here."
              />
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Reward</TH>
                    <TH>Source</TH>
                    <TH className="text-right">Points spent</TH>
                    <TH className="text-right">When</TH>
                  </TR>
                </THead>
                <TBody>
                  {redemptions.map((r) => (
                    <TR key={r.id} className="hover:bg-surface-2/60">
                      <TD className="font-medium">{r.reward.name}</TD>
                      <TD>
                        {r.source === "assigned" ? (
                          <Badge tone="warning">Prize</Badge>
                        ) : (
                          <Badge tone="neutral">Redeemed</Badge>
                        )}
                      </TD>
                      <TD className="text-right font-medium tabular-nums">
                        {r.pointsSpent > 0 ? formatNumber(r.pointsSpent) : "Free"}
                      </TD>
                      <TD className="text-right whitespace-nowrap text-muted">
                        {formatDateTime(r.createdAt)}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </Card>
        </div>

        {/* Right: challenges + details */}
        <div className="space-y-6">
          {/* 5 — Challenges */}
          <Card>
            <CardHeader
              title="Challenges"
              action={
                <AssignChallengeDialog
                  memberId={id}
                  challenges={challenges ?? []}
                  assignedIds={assignedIds}
                />
              }
            />
            <div className="p-4">
              {memberChallenges === undefined ? (
                <ChallengesSkeleton />
              ) : memberChallenges.length === 0 ? (
                <EmptyState
                  icon={<TargetIcon />}
                  title="No challenges"
                  description="Assign a challenge to get this member started."
                />
              ) : (
                <div className="space-y-3">
                  {memberChallenges.map((assignment) => (
                    <MemberChallengeItem
                      key={assignment.id}
                      assignment={assignment}
                      memberId={id}
                    />
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function MessageState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="space-y-6">
      <Link
        href="/members"
        className="inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-foreground"
      >
        <ChevronRightIcon className="rotate-180 text-base" />
        All members
      </Link>
      <Card className="p-6">
        <EmptyState icon={<UsersIcon />} title={title} description={description} />
      </Card>
    </div>
  );
}

function StatTileSkeleton() {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-3">
          <Skeleton className="h-3.5 w-20" />
          <Skeleton className="h-8 w-16" />
        </div>
        <Skeleton className="h-10 w-10 rounded-lg" />
      </div>
    </Card>
  );
}

function TableSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="divide-y divide-line">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-5 py-3.5">
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

function ChallengesSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 2 }).map((_, i) => (
        <div key={i} className="space-y-3 rounded-lg border border-line p-4">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-2 w-full rounded-full" />
          <div className="flex gap-2">
            <Skeleton className="h-8 w-24 rounded-lg" />
            <Skeleton className="h-8 w-24 rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  );
}
