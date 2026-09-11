"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";

import { purchaseProduct } from "@/lib/member/actions";
import { formatPrice } from "@/lib/format";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";

/**
 * One tap, no cart, no quantity picker: the simplest thing that produces a
 * purchase record.
 *
 * `purchaseProduct` is called directly rather than through a `<form action>`,
 * so `revalidatePath` in the action only marks the page's cache stale for the
 * *next* navigation - it does not by itself re-render this already-mounted
 * page. `router.refresh()` is what re-runs the Server Components with fresh
 * data right away, so the spend stats and recent-purchases list update the
 * moment the purchase completes instead of on the next visit.
 */
export function BuyButton({
  productId,
  priceCents,
  currency,
  onPurchased,
  className,
  size = "sm",
}: {
  productId: string;
  priceCents: number;
  currency: string;
  /** Called after a successful purchase - e.g. to close the product modal. */
  onPurchased?: () => void;
  className?: string;
  size?: "xs" | "sm";
}) {
  const toast = useToast();
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  const buy = () => {
    startTransition(async () => {
      const res = await purchaseProduct(productId);
      if (res.ok) {
        toast.success(`Purchased for ${formatPrice(priceCents, currency)}.`);
        router.refresh();
        onPurchased?.();
      } else {
        toast.error(res.error ?? "Something went wrong.");
      }
    });
  };

  return (
    <Button size={size} onClick={buy} loading={pending} className={className}>
      Buy
    </Button>
  );
}
