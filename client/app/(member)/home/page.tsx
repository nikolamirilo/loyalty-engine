import type { Metadata } from "next";

import { CampaignLauncher } from "@/components/campaigns/CampaignLauncher";

export const metadata: Metadata = { title: "Home - Loyalty App" };
export const dynamic = "force-dynamic";

export default function HomePage() {
  // The session is gated by the proxy and re-checked in MemberLayout, which
  // also resolves the member id the campaign needs.
  return <CampaignLauncher />;
}
