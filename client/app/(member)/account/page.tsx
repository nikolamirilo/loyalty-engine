import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { getMember, getMemberPrograms } from "@/lib/api";
import { getSessionMemberId } from "@/lib/memberAuth/session";
import { memberProgramId } from "@/lib/server/program";
import type { MemberProgram } from "@/lib/types";
import { Avatar } from "@/components/ui/Avatar";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { CopyIdButton } from "@/components/account/CopyIdButton";
import { EditProfileButton } from "@/components/account/EditProfileButton";
import { ProgramSwitcher } from "@/components/account/ProgramSwitcher";
import { TierBadge } from "@/components/account/TierBadge";
import { CheckCircleIcon, InfoIcon } from "@/components/ui/icons";

export const metadata: Metadata = { title: "Account - Loyalty App" };
export const dynamic = "force-dynamic";

/** One labelled line in the details list. */
function DetailRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="px-4 py-2.5">
      <dt className="text-xs text-faint">{label}</dt>
      <dd className="mt-1 text-sm text-foreground">{children}</dd>
    </div>
  );
}

export default async function AccountPage() {
  // The proxy and MemberLayout already gate this route; this is defense-in-depth.
  const memberId = await getSessionMemberId();
  if (!memberId) redirect("/login");

  const programId = await memberProgramId();
  const member = await getMember(memberId, programId);
  // The switcher is a convenience: if the list cannot be fetched the rest of
  // the page is still worth rendering.
  const programs = await getMemberPrograms(memberId, programId).catch(
    () => [] as MemberProgram[],
  );
  // A cleared phone comes back as "" rather than null (the API can't unset the
  // column), so treat both as "no number on file".
  const phone = member.phone?.trim() ? member.phone : null;

  return (
    <div className="space-y-6">
      <PageHeader title="Account" description="Your profile and program." />

      {/* Null while the member is below the lowest threshold, or when no
          tiers are configured - nothing to celebrate, so render nothing. */}
      {member.tier && <TierBadge tier={member.tier} />}

      <Card>
        {/* No card header: the page is already titled "Account", so a "Profile"
            heading above the only profile on screen just costs a row. The
            actions are icons beside the person they act on instead. */}
        <div className="flex items-center gap-3 px-4 py-3">
          {/* Default size on purpose: `cn` is a plain join, not tailwind-merge,
              so a height or width override would not replace the base classes -
              both would ship and the winner would depend on Tailwind's
              emission order. */}
          <Avatar name={member.name} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-foreground">
              {member.name}
            </p>
            {/* Verification rides with the address rather than taking a row of
                its own: it decides whether a sign-in code can reach them, so it
                means nothing apart from the email it qualifies. */}
            <p className="flex min-w-0 items-center gap-1.5">
              <span className="truncate text-[0.8125rem] text-muted">{member.email}</span>
              {/* The icon stays decorative and the state is carried by text:
                  every icon here hard-sets `aria-hidden` before spreading
                  props, so an `aria-label` on one would sit on an element
                  assistive tech is already told to skip. */}
              {member.isEmailVerified ? (
                <CheckCircleIcon className="shrink-0 text-[0.8125rem] text-success-fg" />
              ) : (
                <InfoIcon className="shrink-0 text-[0.8125rem] text-warning-fg" />
              )}
              <span className="sr-only">
                {member.isEmailVerified ? "Email verified" : "Email not verified"}
              </span>
            </p>
          </div>
          {/* Both actions for this person, together, beside them. The id itself
              is never rendered - it is a support handle, not something a member
              reads, and a 36-character UUID would cost a line of the screen to
              say nothing. Copying still hands over the exact value. */}
          <div className="flex shrink-0 items-center gap-1.5">
            <CopyIdButton id={member.id} />
            <EditProfileButton member={member} />
          </div>
        </div>

        <dl className="border-t border-line">
          <DetailRow label="Phone">
            {phone ?? <span className="text-faint">Not set</span>}
          </DetailRow>
        </dl>
      </Card>

      {/* Renders nothing when there is nowhere to switch to, card and all. */}
      <ProgramSwitcher programs={programs} currentMemberId={member.id} />
    </div>
  );
}
