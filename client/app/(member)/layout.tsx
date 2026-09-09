import { redirect } from "next/navigation";

import { MemberShell } from "@/components/layout/MemberShell";
import { getSessionMemberId } from "@/lib/memberAuth/session";

export const dynamic = "force-dynamic";

export default async function MemberLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // The proxy is the primary gate; this re-check guards the initial render and
  // keeps the tab shell protected even if the proxy matcher ever changes.
  const memberId = await getSessionMemberId();
  if (!memberId) redirect("/login");

  // The shell owns the campaign (see CampaignContext) so it survives tab
  // switches, which is why the member id is resolved here rather than in the
  // Home page.
  return <MemberShell memberId={memberId}>{children}</MemberShell>;
}
