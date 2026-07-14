import Link from "next/link";
import { notFound } from "next/navigation";

import { deleteMember, updateMember } from "@/lib/actions";
import {
  ApiError,
  getChallenges,
  getMember,
  getMemberChallenges,
  getRedemptions,
  getRewards,
  getTiers,
  getTransactions,
} from "@/lib/api";
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
import { StatTile } from "@/components/ui/StatTile";
import { TransactionBadge } from "@/components/ui/StatusBadge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { AssignChallengeDialog } from "@/components/members/AssignChallengeDialog";
import { GrantRewardDialog } from "@/components/members/GrantRewardDialog";
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
} from "@/components/ui/icons";

export default async function MemberPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let member;
  try {
    member = await getMember(id);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }

  const [tiers, transactions, redemptions, memberChallenges, rewards, challenges] =
    await Promise.all([
      getTiers(),
      getTransactions(id),
      getRedemptions(id),
      getMemberChallenges(id),
      getRewards(true),
      getChallenges(true),
    ]);

  const tier = memberTier(tiers, member);
  const totalEarned = transactions
    .filter((t) => t.type === "earn")
    .reduce((sum, t) => sum + t.points, 0);
  const completedChallenges = memberChallenges.filter(
    (c) => c.status === "completed",
  ).length;
  const assignedIds = memberChallenges.map((c) => c.challenge_id);

  return (
    <div className="space-y-6">
      <Link
        href="/members"
        className="inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-foreground"
      >
        <ChevronRightIcon className="rotate-180 text-base" />
        All members
      </Link>

      {/* Profile + actions */}
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
                {tier ? (
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
            />
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-line pt-5">
          <span className="mr-1 text-sm font-medium text-muted">Points:</span>
          <PointsActions memberId={member.id} />
          <div className="mx-1 h-5 w-px bg-line" />
          <GrantRewardDialog
            memberId={member.id}
            rewards={rewards}
            balance={member.pointsBalance}
          />
        </div>
      </Card>

      {/* Stat tiles */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Points balance"
          value={member.pointsBalance}
          icon={<CoinsIcon />}
          accent="blue"
        />
        <StatTile
          label="Lifetime earned"
          value={totalEarned}
          icon={<CoinsIcon />}
          accent="aqua"
        />
        <StatTile
          label="Challenges completed"
          value={`${completedChallenges}/${memberChallenges.length}`}
          icon={<TargetIcon />}
          accent="violet"
        />
        <StatTile
          label="Redemptions"
          value={redemptions.length}
          icon={<GiftIcon />}
          accent="orange"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: history */}
        <div className="space-y-6 lg:col-span-2">
          <Card className="overflow-hidden">
            <CardHeader
              title="Points activity"
              description="Earn, burn, and adjustment history"
            />
            {transactions.length === 0 ? (
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
                        {t.description ?? "—"}
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

          <Card className="overflow-hidden">
            <CardHeader
              title="Redemptions & prizes"
              description="Rewards redeemed for points or assigned for free"
            />
            {redemptions.length === 0 ? (
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
          <Card>
            <CardHeader
              title="Challenges"
              action={
                <AssignChallengeDialog
                  memberId={member.id}
                  challenges={challenges}
                  assignedIds={assignedIds}
                />
              }
            />
            <div className="p-4">
              {memberChallenges.length === 0 ? (
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
                      memberId={member.id}
                    />
                  ))}
                </div>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Details" />
            <dl className="divide-y divide-line text-sm">
              <DetailRow label="Email" value={member.email} />
              <DetailRow label="Phone" value={member.phone ?? "—"} />
              <DetailRow
                label="Segments"
                value={member.segments.length ? member.segments.join(", ") : "—"}
              />
              <DetailRow label="Member ID" value={member.id} mono />
            </dl>
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
