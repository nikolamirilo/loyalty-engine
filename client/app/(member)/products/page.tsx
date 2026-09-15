import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { getMemberPurchases, getProducts, getPurchaseStats } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { getSessionMemberId } from "@/lib/memberAuth/session";
import { memberProgramId } from "@/lib/server/program";
import { ProductCatalog } from "@/components/products/ProductCatalog";
import { PurchaseHistory } from "@/components/products/PurchaseHistory";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatTile } from "@/components/ui/StatTile";
import { Tabs } from "@/components/ui/Tabs";
import { CoinsIcon, ShoppingBagIcon } from "@/components/ui/icons";

export const metadata: Metadata = { title: "Products - Loyalty App" };
export const dynamic = "force-dynamic";

/** Window the "spend" stat tile reports over - matches the campaign-facing
 * `GET /members/{id}/purchase-stats?days=` default. */
const STATS_PERIOD_DAYS = 7;

export default async function ProductsPage() {
  // The proxy and MemberLayout already gate this route; this is defense-in-depth.
  const memberId = await getSessionMemberId();
  if (!memberId) redirect("/login");

  const programId = await memberProgramId();
  const [products, purchases, stats] = await Promise.all([
    getProducts(true, programId),
    getMemberPurchases(memberId, programId),
    getPurchaseStats(memberId, STATS_PERIOD_DAYS, programId),
  ]);

  return (
    <div className="space-y-6">
      <PageHeader title="Products" description="Browse and buy with your card on file." />

      <div className="grid grid-cols-2 gap-4">
        <StatTile
          size="sm"
          label={`Spent (${STATS_PERIOD_DAYS}d)`}
          value={formatPrice(stats.periodSpendCents, stats.currency)}
          sub={`${stats.periodPurchaseCount} purchase${stats.periodPurchaseCount === 1 ? "" : "s"}`}
          icon={<CoinsIcon />}
          accent="yellow"
        />
        <StatTile
          size="sm"
          label="Total spent"
          value={formatPrice(stats.totalSpendCents, stats.currency)}
          sub={`${stats.purchaseCount} purchase${stats.purchaseCount === 1 ? "" : "s"} all-time`}
          icon={<ShoppingBagIcon />}
          accent="aqua"
        />
      </div>

      <Tabs
        tabs={[
          {
            value: "catalogue",
            label: "Catalogue",
            content: <ProductCatalog products={products} />,
          },
          {
            value: "history",
            label: "Purchase history",
            content: <PurchaseHistory purchases={purchases} />,
          },
        ]}
      />
    </div>
  );
}
