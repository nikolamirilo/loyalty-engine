import type { Product } from "@/lib/types";
import { Checkbox, Field, Input, Textarea } from "@/components/ui/Field";

/** Shared form fields for creating and editing a product. */
export function ProductFields({ product }: { product?: Product }) {
  return (
    <>
      <Field label="Name" htmlFor="product-name">
        <Input
          id="product-name"
          name="name"
          placeholder="e.g. Ethiopia Yirgacheffe Whole Beans, 250g"
          defaultValue={product?.name}
          required
        />
      </Field>
      <Field label="Description" htmlFor="product-desc">
        <Textarea
          id="product-desc"
          name="description"
          placeholder="Details shown to members in the catalog"
          defaultValue={product?.description ?? ""}
        />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Price" htmlFor="product-price" hint={product?.currency ?? "EUR"}>
          <Input
            id="product-price"
            name="price"
            type="number"
            min={0.01}
            step={0.01}
            defaultValue={
              product ? (product.priceCents / 100).toFixed(2) : undefined
            }
            required
          />
        </Field>
        <Field label="Category" htmlFor="product-category" help="Optional grouping">
          <Input
            id="product-category"
            name="category"
            placeholder="e.g. coffee"
            defaultValue={product?.category ?? ""}
          />
        </Field>
      </div>
      <Checkbox
        name="isActive"
        label="Active (visible to members)"
        defaultChecked={product ? product.isActive : true}
      />
    </>
  );
}
