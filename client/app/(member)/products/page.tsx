import type { Metadata } from "next";

import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { PackageIcon } from "@/components/ui/icons";

export const metadata: Metadata = { title: "Products - Loyalty Engine" };

export default function ProductsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Products" description="Browse what you can redeem." />
      <Card>
        <EmptyState
          icon={<PackageIcon />}
          title="Coming soon"
          description="Products and rewards you can redeem will show up here."
        />
      </Card>
    </div>
  );
}
