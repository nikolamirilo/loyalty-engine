"use client";

import Link from "next/link";

import { usePreload } from "@/lib/swr/preload";
import { cn, formatNumber } from "@/lib/format";
import type { Member } from "@/lib/types";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { ChevronRightIcon } from "@/components/ui/icons";

const CHECKBOX = "h-4 w-4 cursor-pointer rounded border-line accent-primary";

/**
 * Presentational members table. The parent (MembersView) supplies the already
 * paginated + searched page of members, owns the search box and pager, and
 * owns which members are selected - this component just renders rows.
 */
export function MembersTable({
  members,
  selected,
  onToggle,
  onToggleAll,
}: {
  members: Member[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  /** Selects every row on this page, or clears them if all are selected. */
  onToggleAll: () => void;
}) {
  const preload = usePreload();
  const allSelected = members.every((m) => selected.has(m.id));
  return (
    <Table>
      <THead>
        <TR>
          <TH className="w-10 pr-0">
            <input
              type="checkbox"
              className={CHECKBOX}
              checked={allSelected}
              onChange={onToggleAll}
              aria-label={allSelected ? "Clear selection on this page" : "Select all on this page"}
            />
          </TH>
          <TH>Member</TH>
          <TH>Tier</TH>
          <TH>Segments</TH>
          <TH>Balance</TH>
          <TH className="w-8" />
        </TR>
      </THead>
      <TBody>
        {members.map((member) => {
          const tier = member.tier;
          return (
            <TR
              key={member.id}
              className={cn(
                "group hover:bg-surface-2/60",
                selected.has(member.id) && "bg-primary/5",
              )}
            >
              <TD className="w-10 pr-0">
                <input
                  type="checkbox"
                  className={CHECKBOX}
                  checked={selected.has(member.id)}
                  onChange={() => onToggle(member.id)}
                  aria-label={`Select ${member.name}`}
                />
              </TD>
              <TD>
                <Link
                  href={`/admin/members/${member.id}`}
                  onMouseEnter={() => preload.member(member.id)}
                  onFocus={() => preload.member(member.id)}
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
                  <span className="text-xs text-faint">-</span>
                )}
              </TD>
              <TD>
                <div className="flex flex-wrap gap-1">
                  {member.segments.length ? (
                    member.segments.slice(0, 3).map((s) => (
                      <Badge key={s.id} tone="neutral">
                        {s.name}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-xs text-faint">-</span>
                  )}
                  {member.segments.length > 3 && (
                    <Badge tone="neutral">+{member.segments.length - 3}</Badge>
                  )}
                </div>
              </TD>
              <TD className="font-semibold tabular-nums whitespace-nowrap">
                {formatNumber(member.pointsBalance)}
                <span className="ml-1 text-xs font-normal text-faint">pts</span>
              </TD>
              <TD>
                <Link
                  href={`/admin/members/${member.id}`}
                  aria-label={`Open ${member.name}`}
                  className="flex text-faint transition-colors group-hover:text-foreground"
                >
                  <ChevronRightIcon className="text-base" />
                </Link>
              </TD>
            </TR>
          );
        })}
      </TBody>
    </Table>
  );
}
