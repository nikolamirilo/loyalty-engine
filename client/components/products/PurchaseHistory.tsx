import type { Purchase } from "@/lib/types";
import { formatDateTime, formatPrice } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ShoppingBagIcon } from "@/components/ui/icons";

/** The "Purchase history" tab: every purchase this member has made, newest
 * first. The tab label itself already says what this is, so the card has no
 * heading of its own. */
export function PurchaseHistory({ purchases }: { purchases: Purchase[] }) {
  return (
    <Card>
      {purchases.length === 0 ? (
        <EmptyState
          icon={<ShoppingBagIcon />}
          title="No purchases yet"
          description="Products you buy will show up here."
        />
      ) : (
        <ul className="divide-y divide-line">
          {purchases.map((purchase) => (
            <li key={purchase.id} className="flex items-center gap-3 px-5 py-4">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-aqua/12 text-lg text-accent-aqua">
                <ShoppingBagIcon />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {purchase.productName}
                </p>
                <p className="text-xs text-faint">{formatDateTime(purchase.createdAt)}</p>
              </div>
              <p className="shrink-0 text-sm font-medium tabular-nums text-foreground">
                {formatPrice(purchase.totalCents, purchase.currency)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
