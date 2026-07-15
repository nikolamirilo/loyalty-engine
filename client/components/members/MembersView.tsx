"use client";

import { useEffect, useState } from "react";

import { useMembers, useMembersCount, useTiers } from "@/lib/swr/hooks";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Field";
import { Pagination } from "@/components/ui/Pagination";
import { Skeleton } from "@/components/ui/Skeleton";
import { MembersTable } from "./MembersTable";
import { SearchIcon, UsersIcon } from "@/components/ui/icons";

const PAGE_SIZE = 10;

/**
 * Searchable, paginated members list backed by SWR. Search is debounced and
 * runs server-side (so it spans the whole dataset, not just the current page);
 * `keepPreviousData` (set globally) keeps the current rows visible while the
 * next page loads, so paging feels instant.
 */
export function MembersView() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [page, setPage] = useState(0);

  // Debounce the search box; reset to the first page whenever the term changes.
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim());
      setPage(0);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const q = debouncedQuery || undefined;
  const { data: members, error, isLoading } = useMembers({
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    q,
  });
  const { data: countData } = useMembersCount(q);
  const { data: tiers } = useTiers();

  const total = countData?.count ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <Card className="overflow-hidden p-0">
      <div className="border-b border-line p-3">
        <div className="relative max-w-sm">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-base text-faint" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or email…"
            className="pl-9"
            aria-label="Search members"
          />
        </div>
      </div>

      {error ? (
        <EmptyState
          icon={<UsersIcon />}
          title="Couldn't load members"
          description={(error as Error)?.message ?? "Please try again."}
        />
      ) : isLoading && !members ? (
        <MembersTableSkeleton />
      ) : members && members.length > 0 ? (
        <>
          <MembersTable members={members} tiers={tiers ?? []} />
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      ) : (
        <EmptyState
          icon={<UsersIcon />}
          title={debouncedQuery ? "No matching members" : "No members yet"}
          description={
            debouncedQuery
              ? "Try a different search term."
              : "Add your first member to get started."
          }
        />
      )}
    </Card>
  );
}

function MembersTableSkeleton() {
  return (
    <div className="divide-y divide-line">
      {Array.from({ length: PAGE_SIZE }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-5 py-4">
          <Skeleton className="h-9 w-9 rounded-full" />
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-3 w-56" />
          </div>
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-4 w-12" />
        </div>
      ))}
    </div>
  );
}
