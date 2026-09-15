import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { getMember, getMemberPrograms } from "@/lib/api";
import { getSessionMemberId } from "@/lib/memberAuth/session";
import { memberProgramId } from "@/lib/server/program";
import type { MemberProgram } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { CopyIdButton } from "@/components/account/CopyIdButton";
import { EditProfileButton } from "@/components/account/EditProfileButton";
import { ProgramSwitcher } from "@/components/account/ProgramSwitcher";

export const metadata: Metadata = { title: "Account - Loyalty App" };
export const dynamic = "force-dynamic";

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
      <PageHeader title="Account" description="Your basic information." />
      <Card className="p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="min-w-0">
            <h2 className="truncate text-lg font-semibold tracking-tight text-foreground">
              {member.name}
            </h2>
            <p className="truncate text-sm text-muted">{member.email}</p>
          </div>
          <div className="flex items-center gap-2 sm:ml-auto sm:shrink-0">
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

        <ProgramSwitcher programs={programs} currentMemberId={member.id} />
      </Card>
    </div>
  );
}
