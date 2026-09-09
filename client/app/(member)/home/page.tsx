import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { getSessionMemberId } from "@/lib/memberAuth/session";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { HomeIcon } from "@/components/ui/icons";
import { CampaignLauncher } from "@/components/campaigns/CampaignLauncher";

export const metadata: Metadata = { title: "Home - Loyalty Engine" };
export const dynamic = "force-dynamic";

export default async function HomePage() {
  // The proxy and MemberLayout already gate this route; this is defense-in-depth.
  const memberId = await getSessionMemberId();
  if (!memberId) redirect("/login");

  return (
    <div className="space-y-6">
      <PageHeader title="Home" description="Your loyalty overview." />
      <CampaignLauncher memberId={memberId} />
      <Card>
        <EmptyState
          icon={<HomeIcon />}
          title="Coming soon"
          description="Your points, tier, and activity will show up here."
        />
      </Card>
    </div>
  );
}
