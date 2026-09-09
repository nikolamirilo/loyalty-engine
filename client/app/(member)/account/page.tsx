import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { getMember } from "@/lib/api";
import { getSessionMemberId } from "@/lib/memberAuth/session";
import { Avatar } from "@/components/ui/Avatar";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { CopyIdButton } from "@/components/account/CopyIdButton";

export const metadata: Metadata = { title: "Account - Loyalty Engine" };
export const dynamic = "force-dynamic";

export default async function AccountPage() {
  // The proxy and MemberLayout already gate this route; this is defense-in-depth.
  const memberId = await getSessionMemberId();
  if (!memberId) redirect("/login");

  const member = await getMember(memberId);

  return (
    <div className="space-y-6">
      <PageHeader title="Account" description="Your basic information." />
      <Card className="p-6">
        <div className="flex items-center gap-4">
          <Avatar name={member.name} className="h-14 w-14 text-base" />
          <div className="min-w-0">
            <h2 className="text-lg font-semibold tracking-tight text-foreground">
              {member.name}
            </h2>
            <p className="text-sm text-muted">{member.email}</p>
          </div>
        </div>

        <dl className="mt-5 space-y-5 border-t border-line pt-5">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <dt className="text-xs text-faint">User ID</dt>
              <dd className="mt-1 truncate text-sm text-foreground">{member.id}</dd>
            </div>
            <CopyIdButton id={member.id} />
          </div>
          <div>
            <dt className="text-xs text-faint">Email</dt>
            <dd className="mt-1 text-sm text-foreground">{member.email}</dd>
          </div>
          <div>
            <dt className="text-xs text-faint">Phone</dt>
            <dd className="mt-1 text-sm text-foreground">
              {member.phone ?? <span className="text-faint">-</span>}
            </dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
