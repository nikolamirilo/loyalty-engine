"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import { formatNumber, memberTier } from "@/lib/format";
import type { Member, Tier } from "@/lib/types";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Field";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { ChevronRightIcon, SearchIcon, UsersIcon } from "@/components/ui/icons";

export function MembersTable({
  members,
  tiers,
}: {
  members: Member[];
  tiers: Tier[];
}) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return members;
    return members.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.email.toLowerCase().includes(q) ||
        m.segments.some((s) => s.toLowerCase().includes(q)),
    );
  }, [members, query]);

  return (
    <div>
      <div className="border-b border-line p-3">
        <div className="relative max-w-sm">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-base text-faint" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, email, or segment…"
            className="pl-9"
            aria-label="Search members"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<UsersIcon />}
          title={query ? "No matching members" : "No members yet"}
          description={
            query
              ? "Try a different search term."
              : "Add your first member to get started."
          }
        />
      ) : (
        <Table>
          <THead>
            <TR>
              <TH>Member</TH>
              <TH>Tier</TH>
              <TH>Segments</TH>
              <TH className="text-right">Balance</TH>
              <TH className="w-8" />
            </TR>
          </THead>
          <TBody>
            {filtered.map((member) => {
              const tier = memberTier(tiers, member);
              return (
                <TR
                  key={member.id}
                  className="group hover:bg-surface-2/60"
                >
                  <TD>
                    <Link
                      href={`/members/${member.id}`}
                      className="flex items-center gap-3"
                    >
                      <Avatar name={member.name} />
                      <span className="min-w-0">
                        <span className="block truncate font-medium text-foreground group-hover:text-primary">
                          {member.name}
                        </span>
                        <span className="block truncate text-xs text-muted">
                          {member.email}
                        </span>
                      </span>
                    </Link>
                  </TD>
                  <TD>
                    {tier ? (
                      <Badge tone="primary">{tier.name}</Badge>
                    ) : (
                      <span className="text-xs text-faint">—</span>
                    )}
                  </TD>
                  <TD>
                    <div className="flex flex-wrap gap-1">
                      {member.segments.length ? (
                        member.segments.slice(0, 3).map((s) => (
                          <Badge key={s} tone="neutral">
                            {s}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-xs text-faint">—</span>
                      )}
                      {member.segments.length > 3 && (
                        <Badge tone="neutral">
                          +{member.segments.length - 3}
                        </Badge>
                      )}
                    </div>
                  </TD>
                  <TD className="text-right font-semibold tabular-nums whitespace-nowrap">
                    {formatNumber(member.pointsBalance)}
                    <span className="ml-1 text-xs font-normal text-faint">
                      pts
                    </span>
                  </TD>
                  <TD>
                    <Link
                      href={`/members/${member.id}`}
                      aria-label={`Open ${member.name}`}
                      className="flex justify-end text-faint transition-colors group-hover:text-foreground"
                    >
                      <ChevronRightIcon className="text-base" />
                    </Link>
                  </TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      )}
    </div>
  );
}
