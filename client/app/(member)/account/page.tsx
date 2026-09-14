import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { getMember } from "@/lib/api";
import { getSessionMemberId } from "@/lib/memberAuth/session";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { CopyIdButton } from "@/components/account/CopyIdButton";
import { EditProfileButton } from "@/components/account/EditProfileButton";
import { TierBadge } from "@/components/account/TierBadge";

export const metadata: Metadata = { title: "Account - Loyalty App" };
export const dynamic = "force-dynamic";

export default async function AccountPage() {
  // The proxy and MemberLayout already gate this route; this is defense-in-depth.
  const memberId = await getSessionMemberId();
  if (!memberId) redirect("/login");

  const member = await getMember(memberId);
  // A cleared phone comes back as "" rather than null (the API can't unset the
  // column), so treat both as "no number on file".
  const phone = member.phone?.trim() ? member.phone : null;

  return (
    <div className="space-y-6">
      <PageHeader title="Account" description="Your basic information." />

      {/* Null while the member is below the lowest threshold, or when no
          tiers are configured - nothing to celebrate, so render nothing. */}
      {member.tier && <TierBadge tier={member.tier} />}
      <Card className="p-6">
        {/* Actions stack under the email rather than sitting beside it: this
            view always renders at phone width, and `sm:` is a viewport query,
            so a side-by-side row would misfire inside the desktop frame. */}
        <div className="flex flex-col gap-4">
          <div className="min-w-0">
            <h2 className="truncate text-lg font-semibold tracking-tight text-foreground">
              {member.name}
            </h2>
            <p className="truncate text-sm text-muted">{member.email}</p>
          </div>
          <div className="flex items-center gap-2">
            <CopyIdButton id={member.id} />
            <EditProfileButton member={member} />
          </div>
        </div>

        <dl className="mt-5 space-y-5 border-t border-line pt-5">
          <div>
            <dt className="text-xs text-faint">Name</dt>
            <dd className="mt-1 text-sm text-foreground">{member.name}</dd>
          </div>
          <div>
            <dt className="text-xs text-faint">Email</dt>
            <dd className="mt-1 text-sm text-foreground">{member.email}</dd>
          </div>
          <div>
            <dt className="text-xs text-faint">Phone</dt>
            <dd className="mt-1 text-sm text-foreground">
              {phone ?? <span className="text-faint">-</span>}
            </dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
