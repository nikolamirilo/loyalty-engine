"use client";

import { useTransition } from "react";

import { deleteProduct, setProductActive, updateProduct } from "@/lib/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import { formatPrice } from "@/lib/format";
import type { Product } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { DropdownMenu, DropdownMenuItem } from "@/components/ui/DropdownMenu";
import { FormDialog } from "@/components/ui/FormDialog";
import { ActiveBadge } from "@/components/ui/StatusBadge";
import { TD, TR } from "@/components/ui/Table";
import { useToast } from "@/components/ui/Toast";
import {
  BanIcon,
  CheckIcon,
  CopyIcon,
  MoreVerticalIcon,
  PencilIcon,
  TrashIcon,
} from "@/components/ui/icons";
import { ProductFields } from "./ProductFields";

function EditProductMenuItem({ product }: { product: Product }) {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <DropdownMenuItem>
          <PencilIcon /> Edit
        </DropdownMenuItem>
      }
      title="Edit product"
      action={updateProduct}
      submitLabel="Save changes"
      onSuccess={() => revalidate.products()}
    >
      <input type="hidden" name="id" value={product.id} />
      <ProductFields product={product} />
    </FormDialog>
  );
}

export function ProductRow({ product }: { product: Product }) {
  const revalidate = useRevalidate();
  const toast = useToast();
  const [togglePending, startToggle] = useTransition();

  const copyId = async () => {
    try {
      await navigator.clipboard.writeText(product.id);
      toast.success("Product ID copied.");
    } catch {
      toast.error("Couldn't copy product ID.");
    }
  };

  const toggleActive = () => {
    startToggle(async () => {
      const res = await setProductActive(product.id, !product.isActive);
      if (res.ok) {
        toast.success(product.isActive ? "Product deactivated." : "Product activated.");
        revalidate.products();
      } else {
        toast.error(res.error ?? "Something went wrong.");
      }
    });
  };

  return (
    <TR className="hover:bg-surface-2/60">
      <TD>
        <div className="font-medium text-foreground">{product.name}</div>
        {product.description && (
          <div className="mt-0.5 line-clamp-1 max-w-md text-xs text-muted">
            {product.description}
          </div>
        )}
      </TD>
      <TD className="font-medium tabular-nums whitespace-nowrap">
        {formatPrice(product.priceCents, product.currency)}
      </TD>
      <TD className="whitespace-nowrap text-muted">
        {product.category ?? <span className="text-faint">-</span>}
      </TD>
      <TD>
        <ActiveBadge active={product.isActive} />
      </TD>
      <TD>
        <div className="flex">
          <DropdownMenu
            trigger={
              <Button variant="ghost" size="icon" aria-label={`Actions for ${product.name}`}>
                <MoreVerticalIcon />
              </Button>
            }
          >
            <DropdownMenuItem onClick={toggleActive} disabled={togglePending}>
              {product.isActive ? (
                <>
                  <BanIcon /> Deactivate
                </>
              ) : (
                <>
                  <CheckIcon /> Activate
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={copyId}>
              <CopyIcon /> Copy ID
            </DropdownMenuItem>
            <EditProductMenuItem product={product} />
            <ConfirmButton
              trigger={
                <DropdownMenuItem danger>
                  <TrashIcon /> Delete
                </DropdownMenuItem>
              }
              title={`Delete "${product.name}"?`}
              description="This removes the product from the catalog. Existing purchase history is kept."
              confirmLabel="Delete product"
              action={deleteProduct.bind(null, product.id)}
              successMessage="Product deleted."
              onSuccess={() => revalidate.products()}
            />
          </DropdownMenu>
        </div>
      </TD>
    </TR>
  );
}
