"use client";

import { useActionState, useEffect, useState } from "react";
import dynamic from "next/dynamic";

import { deleteMember, updateMember } from "@/lib/actions";
import { idleState } from "@/lib/action-state";
import { formatDateTime } from "@/lib/format";
import { useSegments } from "@/lib/swr/hooks";
import type { Member, Reward, Tier } from "@/lib/types";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Checkbox, Input } from "@/components/ui/Field";
import { Skeleton } from "@/components/ui/Skeleton";
import { SubmitButton } from "@/components/ui/SubmitButton";
import { VerifiedBadge } from "@/components/ui/StatusBadge";
import { useToast } from "@/components/ui/Toast";
import {
  CopyIcon,
  LayersIcon,
  PencilIcon,
  TagIcon,
  TrashIcon,
} from "@/components/ui/icons";
import { CustomAttributeFields } from "@/components/members/CustomAttributeFields";
import { CustomAttributeList } from "@/components/members/CustomAttributeList";
import { PointsActions } from "@/components/members/PointsActions";

// Interaction-only dialog, lazy-loaded so its chunk (and the reward list
// inside) isn't in the initial member-detail bundle.
const GrantRewardDialog = dynamic(
  () =>
    import("@/components/members/GrantRewardDialog").then(
      (m) => m.GrantRewardDialog,
    ),
  { ssr: false },
);

/**
 * The member's profile: name/email/phone/segments/custom attributes/tier, all
 * editable in place (no dialog) via a single Save that reuses `updateMember`
 * as-is — it already accepts every one of these fields in one request.
 */
export function MemberProfileCard({
  member,
  tier,
  tiersLoading,
  rewards,
  onMutated,
}: {
  member?: Member;
  tier: Tier | null;
  tiersLoading: boolean;
  rewards: Reward[];
  onMutated: () => void;
}) {
  const [editing, setEditing] = useState(false);

  if (!member) return <ProfileSkeleton />;

  return (
    <ProfileCardForm
      member={member}
      tier={tier}
      tiersLoading={tiersLoading}
      rewards={rewards}
      editing={editing}
      onEdit={() => setEditing(true)}
      onCancel={() => setEditing(false)}
      onSaved={() => setEditing(false)}
      onMutated={onMutated}
    />
  );
}

/**
 * Owns the actual `useActionState` call. Split out from `MemberProfileCard`
 * so the effect below calls the opaque `onSaved` prop rather than a `setState`
 * it owns directly — otherwise every save would trigger a lint error for
 * setting state synchronously inside an effect (see `FormDialog`/`FormBody`
 * for the same split, for the same reason).
 */
function ProfileCardForm({
  member,
  tier,
  tiersLoading,
  rewards,
  editing,
  onEdit,
  onCancel,
  onSaved,
  onMutated,
}: {
  member: Member;
  tier: Tier | null;
  tiersLoading: boolean;
  rewards: Reward[];
  editing: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSaved: () => void;
  onMutated: () => void;
}) {
  const [state, formAction] = useActionState(updateMember, idleState);
  const toast = useToast();

  useEffect(() => {
    if (state.ok) {
      toast.success(state.message ?? "Member updated.");
      onMutated();
      onSaved();
    }
    // Only react to a change in the action's result.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  const copyId = async (memberId: string) => {
    try {
      await navigator.clipboard.writeText(memberId);
      toast.success("Member ID copied.");
    } catch {
      toast.error("Couldn't copy member ID.");
    }
  };

  return (
    <Card className="p-6">
      <form action={formAction}>
        <input type="hidden" name="id" value={member.id} />

        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 flex-1 items-start gap-4">
            <Avatar name={member.name} className="h-14 w-14 text-base" />
            {editing ? (
              <div className="max-w-sm flex-1 space-y-2">
                <Input
                  name="name"
                  defaultValue={member.name}
                  className="text-lg font-semibold"
                  required
                />
                <Input name="email" type="email" defaultValue={member.email} required />
              </div>
            ) : (
              <div className="min-w-0">
                <h1 className="text-xl font-semibold tracking-tight text-foreground">
                  {member.name}
                </h1>
                <p className="text-sm text-muted">{member.email}</p>
                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                  {tiersLoading ? (
                    <Skeleton className="h-5 w-20 rounded-full" />
                  ) : tier ? (
                    <Badge tone="primary">
                      <LayersIcon className="text-[13px]" /> {tier.name}
                    </Badge>
                  ) : (
                    <Badge tone="neutral">No tier</Badge>
                  )}
                  {member.segments.map((s) => (
                    <Badge key={s.id} tone="neutral">
                      <TagIcon className="text-[13px]" /> {s.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="flex shrink-0 gap-2">
            {editing ? (
              <>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={onCancel}
                >
                  Cancel
                </Button>
                <SubmitButton size="sm">Save changes</SubmitButton>
              </>
            ) : (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => copyId(member.id)}
                >
                  <CopyIcon /> Copy ID
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={onEdit}
                >
                  <PencilIcon /> Edit
                </Button>
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
              </>
            )}
          </div>
        </div>

        {editing && state.error && (
          <div className="mt-4">
            <ErrorBanner message={state.error} />
          </div>
        )}

        <dl className="mt-5 flex flex-wrap items-start gap-x-6 gap-y-5 border-t border-line pt-5">
          <ProfileField label="Phone" className="w-40">
            {editing ? (
              <Input name="phone" defaultValue={member.phone ?? ""} />
            ) : (
              member.phone ?? <Empty />
            )}
          </ProfileField>

          <ProfileField
            label="Segments"
            className={editing ? "w-full sm:w-72" : "w-40"}
          >
            {editing ? (
              <SegmentCheckboxes selectedIds={member.segments.map((s) => s.id)} />
            ) : member.segments.length ? (
              member.segments.map((s) => s.name).join(", ")
            ) : (
              <Empty />
            )}
          </ProfileField>

          <ProfileField label="Tier" hint="auto" className="w-40">
            {tiersLoading ? (
              <Skeleton className="h-5 w-16 rounded-full" />
            ) : tier ? (
              <Badge tone="primary">{tier.name}</Badge>
            ) : (
              <Empty />
            )}
            {editing && (
              <p className="mt-1 text-xs text-faint">
                Assigned automatically from points balance.
              </p>
            )}
          </ProfileField>

          <ProfileField label="Email verified" className="w-40">
            {editing ? (
              <Checkbox
                name="email_verified"
                label="Verified"
                defaultChecked={!!member.email_verified_at}
              />
            ) : (
              <div className="flex flex-col items-start gap-1">
                <VerifiedBadge verified={!!member.email_verified_at} />
                {member.email_verified_at && (
                  <span className="text-xs text-faint">
                    {formatDateTime(member.email_verified_at)}
                  </span>
                )}
              </div>
            )}
            {editing && (
              <p className="mt-1 text-xs text-faint">
                Normally set by the DOI email flow; check/uncheck to override.
              </p>
            )}
          </ProfileField>

          {editing ? (
            <CustomAttributeFields member={member} itemClassName="w-40" />
          ) : (
            <CustomAttributeList member={member} itemClassName="w-40" />
          )}
        </dl>
      </form>

      <div
        className={
          "mt-5 flex flex-wrap items-center gap-2 border-t border-line pt-5" +
          (editing ? " pointer-events-none opacity-40" : "")
        }
      >
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
  );
}

function ProfileField({
  label,
  hint,
  className,
  children,
}: {
  label: string;
  hint?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={className}>
      <dt className="mb-1.5 flex items-center gap-1.5 text-xs text-faint">
        {label}
        {hint && <span className="text-faint/70">({hint})</span>}
      </dt>
      <dd className="min-w-0 text-sm text-foreground">{children}</dd>
    </div>
  );
}

function Empty() {
  return <span className="text-faint">-</span>;
}

function SegmentCheckboxes({ selectedIds }: { selectedIds: string[] }) {
  const { data: segments } = useSegments();

  if (segments === undefined) return <p className="text-xs text-faint">Loading segments…</p>;
  if (segments.length === 0) {
    return (
      <p className="text-xs text-faint">
        No segments yet — create one on the Segments page first.
      </p>
    );
  }

  return (
    <div className="flex max-h-32 flex-wrap gap-x-4 gap-y-2 overflow-y-auto rounded-lg border border-line p-3">
      {segments.map((segment) => (
        <Checkbox
          key={segment.id}
          name="segment_ids"
          value={segment.id}
          label={segment.name}
          defaultChecked={selectedIds.includes(segment.id)}
        />
      ))}
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
          <Skeleton className="h-8 w-24 rounded-lg" />
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
