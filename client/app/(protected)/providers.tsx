"use client";

import { SWRConfig } from "swr";

import { fetcher } from "@/lib/swr/fetcher";

/**
 * Client data context for the console. SWRConfig holds the shared cache and the
 * default behaviour every hook inherits:
 *  - one `fetcher` (→ the same-origin `/api/le` proxy),
 *  - `keepPreviousData` so navigations show the last data while revalidating
 *    instead of flashing empty,
 *  - focus revalidation so data freshens when the admin returns to the tab.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        keepPreviousData: true,
        revalidateOnFocus: true,
        dedupingInterval: 5000,
        errorRetryCount: 2,
      }}
    >
      {children}
    </SWRConfig>
  );
}
