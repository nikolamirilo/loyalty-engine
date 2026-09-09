import type { Metadata } from "next";

import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { WalletIcon } from "@/components/ui/icons";

export const metadata: Metadata = { title: "Wallet - Loyalty Engine" };

export default function WalletPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Wallet" description="Your points and redemption history." />
      <Card>
        <EmptyState
          icon={<WalletIcon />}
          title="Coming soon"
          description="Your points balance and past redemptions will show up here."
        />
      </Card>
    </div>
  );
}
