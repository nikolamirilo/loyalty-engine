"use client";

import { createProduct } from "@/lib/actions";
import { useProducts } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { TableRowsSkeleton } from "@/components/ui/Skeletons";
import { ProductFields } from "@/components/products/ProductFields";
import { ProductRow } from "@/components/products/ProductRow";
import { Table, TBody, TH, THead, TR } from "@/components/ui/Table";
import { PlusIcon, ShoppingBagIcon } from "@/components/ui/icons";

function NewProductButton() {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <Button>
          <PlusIcon /> New product
        </Button>
      }
      title="New product"
      description="Add a product members can purchase."
      action={createProduct}
      submitLabel="Create product"
      onSuccess={() => revalidate.products()}
    >
      <ProductFields />
    </FormDialog>
  );
}

export default function ProductsPage() {
  const { data: products } = useProducts();
  const activeCount = products?.filter((p) => p.isActive).length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Products"
        description={
          products && products.length
            ? `${products.length} product${products.length === 1 ? "" : "s"} · ${activeCount} active`
            : "Catalog of products members can purchase."
        }
        actions={<NewProductButton />}
      />

      <Card>
        {products === undefined ? (
          <TableRowsSkeleton />
        ) : products.length === 0 ? (
          <EmptyState
            icon={<ShoppingBagIcon />}
            title="No products yet"
            description="Create your first product so members have something to buy."
            action={<NewProductButton />}
          />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Product</TH>
                <TH>Price</TH>
                <TH>Category</TH>
                <TH>Status</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {products.map((product) => (
                <ProductRow key={product.id} product={product} />
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
