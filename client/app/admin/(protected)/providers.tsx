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
 *
 * The cache is scoped to one program. Cache keys are the upstream path (e.g.
 * "/members?limit=1000"), which is identical across programs, so a shared cache
 * would serve the previous program's rows for a moment after switching - the
 * one failure a viewer would notice mid-demo. Keying this component by
 * `programId` throws the whole cache away on a switch instead.
 */
export function Providers({
  programId,
  children,
}: {
  programId: string;
  children: React.ReactNode;
}) {
  return (
    <SWRConfig
      key={programId}
      value={{
        provider: () => new Map(),
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
