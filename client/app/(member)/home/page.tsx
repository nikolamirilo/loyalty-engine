import type { Metadata } from "next";

import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { HomeIcon } from "@/components/ui/icons";

export const metadata: Metadata = { title: "Home - Loyalty Engine" };

export default function HomePage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Home" description="Your loyalty overview." />
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
