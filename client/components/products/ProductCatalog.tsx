import type { Product } from "@/lib/types";
import { ProductCard } from "@/components/products/ProductCard";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ShoppingBagIcon } from "@/components/ui/icons";

/** The "Catalogue" tab: every active product, two per row. Each tile opens a
 * modal with the full details and the Buy action (see `ProductCard`). */
export function ProductCatalog({ products }: { products: Product[] }) {
  return (
    <Card>
      {products.length === 0 ? (
        <EmptyState
          icon={<ShoppingBagIcon />}
          title="Nothing here yet"
          description="Products will show up here once they're added."
        />
      ) : (
        <div className="grid grid-cols-2 gap-3 p-4">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </Card>
  );
}
