"use client";

import { formatCustomValue } from "@/lib/custom-attributes";
import { useMemberAttributes } from "@/lib/swr/hooks";
import type { Member } from "@/lib/types";

/**
 * Read-only custom attribute values on the member detail page. Driven by the
 * definitions list rather than the member's own keys, so a field with no value
 * still shows (as "-") and a stale key left over from a deleted attribute never
 * does.
 */
export function CustomAttributeList({ member }: { member: Member }) {
  const { data: attributes } = useMemberAttributes();

  if (!attributes || attributes.length === 0) return null;

  return (
    // The separator lives here rather than at the call site so nothing is left
    // behind when there are no attributes and this renders null.
    <dl className="mt-5 grid gap-x-8 gap-y-3 border-t border-line pt-5 sm:grid-cols-2 lg:grid-cols-3">
      {attributes.map((attribute) => {
        const value = formatCustomValue(
          attribute,
          member.custom_attributes?.[attribute.key],
        );
        return (
          <div key={attribute.id} className="min-w-0">
            <dt className="text-xs text-faint">{attribute.label}</dt>
            <dd className="truncate text-sm text-foreground">
              {value ?? <span className="text-faint">-</span>}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}
