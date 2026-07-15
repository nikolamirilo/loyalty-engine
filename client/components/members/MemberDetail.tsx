"use client";

import Link from "next/link";
import dynamic from "next/dynamic";

import { deleteMember, updateMember } from "@/lib/actions";
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
import {
  cn,
  formatDateTime,
  formatNumber,
  memberTier,
  signedNumber,
} from "@/lib/format";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { FormDialog } from "@/components/ui/FormDialog";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatTile } from "@/components/ui/StatTile";
import { TransactionBadge } from "@/components/ui/StatusBadge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { MemberChallengeItem } from "@/components/members/MemberChallengeItem";
import { MemberFields } from "@/components/members/MemberFields";
import { PointsActions } from "@/components/members/PointsActions";
import {
  ChevronRightIcon,
  CoinsIcon,
  GiftIcon,
  LayersIcon,
  PencilIcon,
  TagIcon,
  TargetIcon,
  TrashIcon,
  UsersIcon,
} from "@/components/ui/icons";

// Interaction-only dialogs — lazy-loaded so their chunk (and the reward/
// challenge lists inside) isn't in the initial member-detail bundle.
const GrantRewardDialog = dynamic(
  () =>
    import("@/components/members/GrantRewardDialog").then(
      (m) => m.GrantRewardDialog,
    ),
  { ssr: false },
);
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
    ? memberChallenges.map((c) => c.challenge_id)
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

      {/* 1 — Profile + actions */}
      {member ? (
        <Card className="p-6">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-start gap-4">
              <Avatar name={member.name} className="h-14 w-14 text-base" />
              <div className="min-w-0">
                <h1 className="text-xl font-semibold tracking-tight text-foreground">
                  {member.name}
                </h1>
                <p className="text-sm text-muted">{member.email}</p>
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  {tiers === undefined ? (
                    <Skeleton className="h-5 w-20 rounded-full" />
                  ) : tier ? (
                    <Badge tone="primary">
                      <LayersIcon className="text-[13px]" /> {tier.name}
                    </Badge>
                  ) : (
                    <Badge tone="neutral">No tier</Badge>
                  )}
                  {member.segments.map((s) => (
                    <Badge key={s} tone="neutral">
                      <TagIcon className="text-[13px]" /> {s}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex shrink-0 gap-2">
              <FormDialog
                trigger={
                  <Button variant="secondary" size="sm">
                    <PencilIcon /> Edit
                  </Button>
                }
                title="Edit member"
                action={updateMember}
                submitLabel="Save changes"
                onSuccess={onMutated}
              >
                <input type="hidden" name="id" value={member.id} />
                <MemberFields member={member} />
              </FormDialog>
              <ConfirmButton
                trigger={
                  <Button variant="secondary" size="sm" className="text-danger">
                    <TrashIcon /> Delete
                  </Button>
                }
                title={`Delete ${member.name}?`}
                description="This permanently deletes the member and all of their points, redemptions, and challenge history."
                confirmLabel="Delete member"
                action={deleteMember.bind(null, member.id)}
                redirectTo="/members"
                successMessage="Member deleted."
                onSuccess={onMutated}
              />
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-line pt-5">
            <span className="mr-1 text-sm font-medium text-muted">Points:</span>
            <PointsActions memberId={member.id} />
            <div className="mx-1 h-5 w-px bg-line" />
            <GrantRewardDialog
              memberId={member.id}
              rewards={rewards ?? []}
              balance={member.pointsBalance}
            />
          </div>
        </Card>
      ) : (
        <ProfileSkeleton />
      )}

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
                        {formatDateTime(t.created_at)}
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
                        {r.points_spent > 0 ? formatNumber(r.points_spent) : "Free"}
                      </TD>
                      <TD className="text-right whitespace-nowrap text-muted">
                        {formatDateTime(r.created_at)}
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

          {/* 6 — Details */}
          <Card>
            <CardHeader title="Details" />
            {member ? (
              <dl className="divide-y divide-line text-sm">
                <DetailRow label="Email" value={member.email} />
                <DetailRow label="Phone" value={member.phone ?? "-"} />
                <DetailRow
                  label="Segments"
                  value={member.segments.length ? member.segments.join(", ") : "-"}
                />
                <DetailRow label="Member ID" value={member.id} mono />
              </dl>
            ) : (
              <div className="space-y-3 p-5">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function DetailRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-4 px-5 py-3">
      <dt className="shrink-0 text-muted">{label}</dt>
      <dd
        className={cn(
          "min-w-0 truncate text-right text-foreground",
          mono && "font-mono text-xs text-muted",
        )}
      >
        {value}
      </dd>
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

function ProfileSkeleton() {
  return (
    <Card className="p-6">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          <Skeleton className="h-14 w-14 rounded-full" />
          <div className="space-y-2.5">
            <Skeleton className="h-6 w-44" />
            <Skeleton className="h-4 w-56" />
            <Skeleton className="h-5 w-24 rounded-full" />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20 rounded-lg" />
          <Skeleton className="h-8 w-20 rounded-lg" />
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-2 border-t border-line pt-5">
        <Skeleton className="h-8 w-20 rounded-lg" />
        <Skeleton className="h-8 w-20 rounded-lg" />
        <Skeleton className="h-8 w-32 rounded-lg" />
      </div>
    </Card>
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
