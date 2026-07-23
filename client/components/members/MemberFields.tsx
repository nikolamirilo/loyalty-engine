"use client";

import { useSegments } from "@/lib/swr/hooks";
import type { Member } from "@/lib/types";
import { Checkbox, Field, Input } from "@/components/ui/Field";

/** Shared form fields for creating and editing a member. */
export function MemberFields({ member }: { member?: Member }) {
  const { data: segments } = useSegments();
  const selectedIds = member?.segments.map((s) => s.id) ?? [];

  return (
    <>
      <Field label="Name" htmlFor="member-name">
        <Input
          id="member-name"
          name="name"
          placeholder="Ada Lovelace"
          defaultValue={member?.name}
          required
        />
      </Field>
      <Field label="Email" htmlFor="member-email">
        <Input
          id="member-email"
          name="email"
          type="email"
          placeholder="ada@example.com"
          defaultValue={member?.email}
          required
        />
      </Field>
      <Field label="Phone" htmlFor="member-phone" hint="optional">
        <Input
          id="member-phone"
          name="phone"
          type="tel"
          placeholder="+1 555 0100"
          defaultValue={member?.phone ?? ""}
        />
      </Field>
      <Field label="Segments" hint="optional">
        {segments === undefined ? (
          <p className="text-xs text-faint">Loading segments…</p>
        ) : segments.length === 0 ? (
          <p className="text-xs text-faint">
            No segments yet — create one on the Segments page first.
          </p>
        ) : (
          <div className="flex max-h-40 flex-wrap gap-x-4 gap-y-2 overflow-y-auto rounded-lg border border-line p-3">
            {segments.map((segment) => (
              <Checkbox
                key={segment.id}
                name="segment_ids"
                value={segment.id}
                label={segment.name}
                defaultChecked={selectedIds.includes(segment.id)}
              />
            ))}
          </div>
        )}
      </Field>
    </>
  );
}
