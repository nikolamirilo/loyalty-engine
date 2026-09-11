"use client";

import { useState } from "react";

import type { Product } from "@/lib/types";
import { formatPrice } from "@/lib/format";
import { BuyButton } from "@/components/products/BuyButton";
import { Dialog } from "@/components/ui/Dialog";

/**
 * A catalogue tile: name, price, and a Buy button - no description, so the
 * grid stays scannable. Tapping anywhere on the tile except Buy opens a modal
 * with the rest (description, category) and its own Buy action; the button
 * stops its click from bubbling to the tile so a quick buy doesn't also pop
 * the modal open behind it.
 *
 * The tile is a `div`, not a `button`, because it contains one - a `<button>`
 * inside a `<button>` is invalid HTML and React would otherwise nest them.
 */
export function ProductCard({ product }: { product: Product }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div
        role="button"
        tabIndex={0}
        onClick={() => setOpen(true)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") setOpen(true);
        }}
        className="flex cursor-pointer items-center gap-2 rounded-xl border border-line bg-surface px-4 py-2.5 text-left transition-colors hover:bg-surface-2/60"
      >
        <div className="min-w-0 flex-1">
          {/* Wraps rather than truncating - one product per row, so there's
              room to show the full name instead of clipping it with "...". */}
          <p className="text-xs font-medium text-foreground">{product.name}</p>
          <p className="mt-1 text-sm font-semibold text-foreground">
            {formatPrice(product.priceCents, product.currency)}
          </p>
        </div>
        <div onClick={(e) => e.stopPropagation()} className="shrink-0">
          <BuyButton
            size="xs"
            productId={product.id}
            priceCents={product.priceCents}
            currency={product.currency}
          />
        </div>
      </div>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={product.name}
        size="sm"
        align="center"
      >
        <div className="space-y-4">
          {product.category && (
            <span className="inline-block rounded-full bg-surface-2 px-2.5 py-1 text-xs font-medium text-muted">
              {product.category}
            </span>
          )}
          {product.description && (
            <p className="text-sm text-muted">{product.description}</p>
          )}
          <div className="flex items-center justify-between gap-3 pt-1">
            <p className="text-lg font-semibold text-foreground">
              {formatPrice(product.priceCents, product.currency)}
            </p>
            <BuyButton
              productId={product.id}
              priceCents={product.priceCents}
              currency={product.currency}
              onPurchased={() => setOpen(false)}
            />
          </div>
        </div>
      </Dialog>
    </>
  );
}
