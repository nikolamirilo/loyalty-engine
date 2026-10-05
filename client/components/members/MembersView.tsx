"use client";

import { useEffect, useState } from "react";

import { deleteMembers } from "@/lib/actions";
import { useMembers, useMembersCount } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Field";
import { Pagination } from "@/components/ui/Pagination";
import { Skeleton } from "@/components/ui/Skeleton";
import { MembersTable } from "./MembersTable";
import { SearchIcon, TrashIcon, UsersIcon } from "@/components/ui/icons";

const PAGE_SIZE = 10;

/**
 * Searchable, paginated members list backed by SWR. Search is debounced and
 * runs server-side (so it spans the whole dataset, not just the current page);
 * `keepPreviousData` (set globally) keeps the current rows visible while the
 * next page loads, so paging feels instant.
 *
 * Rows can be selected for bulk delete. The selection survives paging and
 * searching, so members can be picked from several pages at once.
 */
export function MembersView() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const revalidate = useRevalidate();

  // Debounce the search box; reset to the first page whenever the term changes.
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim());
      setPage(0);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const q = debouncedQuery || undefined;
  const { data: countData } = useMembersCount(q);
  const total = countData?.count ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  // A bulk delete can empty the last page, so read the page clamped to one
  // that still exists rather than the one last clicked.
  const currentPage = countData ? Math.min(page, pageCount - 1) : page;

  const { data: members, error, isLoading } = useMembers({
    skip: currentPage * PAGE_SIZE,
    limit: PAGE_SIZE,
    q,
  });

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const toggleAll = () =>
    setSelected((prev) => {
      const next = new Set(prev);
      const onPage = members ?? [];
      const allOn = onPage.every((m) => next.has(m.id));
      for (const m of onPage) {
        if (allOn) next.delete(m.id);
        else next.add(m.id);
      }
      return next;
    });

  const count = selected.size;

  return (
    <Card className="overflow-hidden p-0">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line p-3">
        <div className="relative w-full max-w-sm">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-base text-faint" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or email…"
            className="pl-9"
            aria-label="Search members"
          />
        </div>
        {count > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted">{count} selected</span>
            <Button variant="ghost" size="sm" onClick={() => setSelected(new Set())}>
              Clear
            </Button>
            <ConfirmButton
              trigger={
                <Button variant="danger" size="sm">
                  <TrashIcon /> Delete selected
                </Button>
              }
              title={`Delete ${count} member${count === 1 ? "" : "s"}?`}
              description="This permanently deletes them from every program, with all of their points, redemptions, and challenge history."
              confirmLabel={`Delete ${count} member${count === 1 ? "" : "s"}`}
              action={deleteMembers.bind(null, [...selected])}
              onSuccess={() => {
                setSelected(new Set());
                revalidate.members();
              }}
            />
          </div>
        )}
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
          <MembersTable
            members={members}
            selected={selected}
            onToggle={toggle}
            onToggleAll={toggleAll}
          />
          <Pagination page={currentPage} pageCount={pageCount} onPageChange={setPage} />
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
