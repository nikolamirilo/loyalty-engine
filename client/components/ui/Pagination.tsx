"use client";

import { cn } from "@/lib/format";
import { Button } from "./Button";
import { ChevronRightIcon } from "./icons";

/**
 * Prev / next pager with a "Page X of Y" indicator. `page` is 0-based. Renders
 * nothing when there's only a single page.
 */
export function Pagination({
  page,
  pageCount,
  onPageChange,
  className,
}: {
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
  className?: string;
}) {
  if (pageCount <= 1) return null;

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 border-t border-line px-4 py-3",
        className,
      )}
    >
      <p className="text-sm text-muted">
        Page <span className="font-medium text-foreground">{page + 1}</span> of{" "}
        <span className="font-medium text-foreground">{pageCount}</span>
      </p>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={page <= 0}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronRightIcon className="rotate-180 text-base" /> Prev
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={page >= pageCount - 1}
          onClick={() => onPageChange(page + 1)}
        >
          Next <ChevronRightIcon className="text-base" />
        </Button>
      </div>
    </div>
  );
}
