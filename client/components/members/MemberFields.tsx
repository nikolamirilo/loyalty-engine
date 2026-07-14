import type { Member } from "@/lib/types";
import { Field, Input } from "@/components/ui/Field";
import { TagsInput } from "@/components/ui/TagsInput";

/** Shared form fields for creating and editing a member. */
export function MemberFields({ member }: { member?: Member }) {
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
      <Field
        label="Segments"
        htmlFor="member-segments"
        help="Press Enter or comma to add a segment"
      >
        <TagsInput
          id="member-segments"
          name="segments"
          defaultValue={member?.segments ?? []}
          placeholder="vip, newsletter"
        />
      </Field>
    </>
  );
}
