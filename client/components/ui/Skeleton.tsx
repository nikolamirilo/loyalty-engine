import type { HTMLAttributes } from "react";

import { cn } from "@/lib/format";

/**
 * Animated placeholder block for loading states. Uses the subtle raised surface
 * token so it reads as "content is on the way" in both light and dark mode.
 */
export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-surface-2", className)}
      {...props}
    />
  );
}
