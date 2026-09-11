"use client";

import type { Member } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Field, Input } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { PencilIcon } from "@/components/ui/icons";
import { updateProfile } from "@/lib/member/actions";

/**
 * Pen button on the Account page that opens the member's own profile form.
 *
 * Only the fields a member may change are here (name, email, phone) - segments,
 * points and custom attributes stay admin-only, and `updateProfile` sends just
 * these three regardless of what is posted.
 */
export function EditProfileButton({
  member,
}: {
  member: Pick<Member, "name" | "email" | "phone">;
}) {
  return (
    <FormDialog
      trigger={
        <Button
          variant="secondary"
          size="icon"
          aria-label="Edit profile"
          title="Edit profile"
          className="shrink-0"
        >
          <PencilIcon />
        </Button>
      }
      title="Edit profile"
      description="Update your name, email address and phone number."
      action={updateProfile}
      submitLabel="Save changes"
      size="sm"
      align="center"
    >
      <div className="space-y-4">
        <Field label="Name" htmlFor="profile-name">
          <Input
            id="profile-name"
            name="name"
            defaultValue={member.name}
            autoComplete="name"
            required
          />
        </Field>
        <Field
          label="Email"
          htmlFor="profile-email"
          help="Your sign-in code is sent to this address."
        >
          <Input
            id="profile-email"
            name="email"
            type="email"
            defaultValue={member.email}
            autoComplete="email"
            required
          />
        </Field>
        <Field label="Phone" htmlFor="profile-phone" hint="Optional">
          <Input
            id="profile-phone"
            name="phone"
            type="tel"
            defaultValue={member.phone ?? ""}
            autoComplete="tel"
          />
        </Field>
      </div>
    </FormDialog>
  );
}
