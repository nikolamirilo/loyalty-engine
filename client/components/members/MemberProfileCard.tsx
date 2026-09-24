"use client";

import { useActionState, useEffect, useState } from "react";
import dynamic from "next/dynamic";

import { deleteMember, updateMember } from "@/lib/actions";
import { idleState } from "@/lib/action-state";
import { formatDate, formatDateTime } from "@/lib/format";
import { useSegments } from "@/lib/swr/hooks";
import type { Member, Reward } from "@/lib/types";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Checkbox, Field, Input } from "@/components/ui/Field";
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
import { NotSet, ProfileDetail } from "@/components/members/ProfileDetail";
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
  rewards,
  onMutated,
}: {
  member?: Member;
  rewards: Reward[];
  onMutated: () => void;
}) {
  const [editing, setEditing] = useState(false);

  if (!member) return <ProfileSkeleton />;

  return (
    <ProfileCardForm
      member={member}
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
  rewards,
  editing,
  onEdit,
  onCancel,
  onSaved,
  onMutated,
}: {
  member: Member;
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
                  {member.tier ? (
                    <Badge tone="primary">
                      <LayersIcon className="text-[0.8125rem]" /> {member.tier.name}
                    </Badge>
                  ) : (
                    <Badge tone="neutral">No tier</Badge>
                  )}
                  {member.segments.map((s) => (
                    <Badge key={s.id} tone="neutral">
                      <TagIcon className="text-[0.8125rem]" /> {s.name}
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
                  redirectTo="/admin/members"
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

        {/* Tier and segments are the badges under the name, so the details
            below only hold what the header doesn't already show. */}
        {editing ? (
          <div className="mt-5 grid gap-4 border-t border-line pt-5 sm:grid-cols-2 lg:grid-cols-4">
            <Field label="Phone" htmlFor="member-phone">
              <Input id="member-phone" name="phone" defaultValue={member.phone ?? ""} />
            </Field>
            <Field label="Email" help="Normally set by the verification email.">
              {/* Same height as the inputs beside it, so the row lines up. */}
              <div className="flex h-[2.375rem] items-center">
                <Checkbox
                  name="emailVerified"
                  label="Verified"
                  defaultChecked={!!member.emailVerifiedAt}
                />
              </div>
            </Field>
            <CustomAttributeFields member={member} />
            <Field label="Segments" className="sm:col-span-2 lg:col-span-4">
              <SegmentCheckboxes selectedIds={member.segments.map((s) => s.id)} />
            </Field>
            <p className="text-xs text-faint sm:col-span-2 lg:col-span-4">
              The tier updates on its own from points balance, purchases, segments and custom
              attributes.
            </p>
          </div>
        ) : (
          <dl className="mt-5 grid grid-cols-2 gap-3 border-t border-line pt-5 sm:grid-cols-3 lg:grid-cols-4">
            <ProfileDetail label="Phone">
              {member.phone ? <span className="truncate">{member.phone}</span> : <NotSet />}
            </ProfileDetail>
            <ProfileDetail label="Email">
              <VerifiedBadge verified={!!member.emailVerifiedAt} />
              {member.emailVerifiedAt && (
                <span
                  className="truncate text-xs font-normal text-faint"
                  title={formatDateTime(member.emailVerifiedAt)}
                >
                  {formatDate(member.emailVerifiedAt)}
                </span>
              )}
            </ProfileDetail>
            <CustomAttributeList member={member} />
          </dl>
        )}
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
          name="segmentIds"
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
