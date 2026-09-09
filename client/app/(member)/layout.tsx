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
  if (!(await getSessionMemberId())) redirect("/login");

  return <MemberShell>{children}</MemberShell>;
}
