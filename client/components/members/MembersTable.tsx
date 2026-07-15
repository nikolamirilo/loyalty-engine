"use client";

import Link from "next/link";

import { preloadMember } from "@/lib/swr/preload";
import { formatNumber, memberTier } from "@/lib/format";
import type { Member, Tier } from "@/lib/types";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { ChevronRightIcon } from "@/components/ui/icons";

/**
 * Presentational members table. The parent (MembersView) supplies the already
 * paginated + searched page of members plus the tiers, and owns the search box
 * and pager — this component just renders rows.
 */
export function MembersTable({
  members,
  tiers,
}: {
  members: Member[];
  tiers: Tier[];
}) {
  return (
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
        {members.map((member) => {
          const tier = memberTier(tiers, member);
          return (
            <TR key={member.id} className="group hover:bg-surface-2/60">
              <TD>
                <Link
                  href={`/members/${member.id}`}
                  onMouseEnter={() => preloadMember(member.id)}
                  onFocus={() => preloadMember(member.id)}
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
                      <Badge key={s} tone="neutral">
                        {s}
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
              <TD className="text-right font-semibold tabular-nums whitespace-nowrap">
                {formatNumber(member.pointsBalance)}
                <span className="ml-1 text-xs font-normal text-faint">pts</span>
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
  );
}
