"use client";

import { formatCustomValue } from "@/lib/custom-attributes";
import { useMemberAttributes } from "@/lib/swr/hooks";
import type { Member } from "@/lib/types";
import { NotSet, ProfileDetail } from "@/components/members/ProfileDetail";

/**
 * Read-only custom attribute values, one tile per attribute, meant to be
 * embedded inside a parent `<dl>` grid (see `MemberProfileCard`). Driven by
 * the definitions list rather than the member's own keys, so a field with no
 * value still shows (as "Not set") and a stale key left over from a deleted
 * attribute never does.
 */
export function CustomAttributeList({ member }: { member: Member }) {
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
          <ProfileDetail key={attribute.id} label={attribute.label}>
            {value === null ? (
              <NotSet />
            ) : (
              <span className="truncate" title={value}>
                {value}
              </span>
            )}
          </ProfileDetail>
        );
      })}
    </>
  );
}
