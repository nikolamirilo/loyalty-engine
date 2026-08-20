"use client";

import { cn } from "@/lib/format";
import { formatCustomValue } from "@/lib/custom-attributes";
import { useMemberAttributes } from "@/lib/swr/hooks";
import type { Member } from "@/lib/types";

/**
 * Read-only custom attribute values, one grid item per attribute, meant to be
 * embedded inside a parent `<dl>` grid (see `MemberProfileCard`). Driven by
 * the definitions list rather than the member's own keys, so a field with no
 * value still shows (as "-") and a stale key left over from a deleted
 * attribute never does.
 */
export function CustomAttributeList({
  member,
  itemClassName,
}: {
  member: Member;
  /** Applied to each item's wrapper — lets the caller control per-item width/layout. */
  itemClassName?: string;
}) {
  const { data: attributes } = useMemberAttributes();

  if (!attributes || attributes.length === 0) return null;

  return (
    <>
      {attributes.map((attribute) => {
        const value = formatCustomValue(
          attribute,
          member.customAttributes?.[attribute.key],
        );
        return (
          <div key={attribute.id} className={cn("min-w-0", itemClassName)}>
            <dt className="mb-1.5 text-xs text-faint">{attribute.label}</dt>
            <dd className="truncate text-sm text-foreground">
              {value ?? <span className="text-faint">-</span>}
            </dd>
          </div>
        );
      })}
    </>
  );
}
