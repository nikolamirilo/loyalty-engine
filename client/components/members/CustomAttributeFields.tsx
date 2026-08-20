"use client";

import { useMemberAttributes } from "@/lib/swr/hooks";
import type { CustomAttributeValue, Member, MemberAttribute } from "@/lib/types";
import { Checkbox, Field, Input, Select } from "@/components/ui/Field";

/**
 * One input per admin-defined custom attribute, for the member create/edit form.
 * Renders nothing when no attributes are configured, so the form is unchanged
 * for programs that don't use them.
 *
 * Each field also emits a hidden `custom_keys` input. That marker is what lets
 * the Server Action tell "the admin cleared this field" from "this input was
 * never rendered" — `FormData.get()` returns null for both, and they mean
 * opposite things (clear the value vs. leave it alone). Without it, saving
 * before the definitions load would wipe every custom value on the member.
 */
export function CustomAttributeFields({
  member,
  itemClassName,
}: {
  member?: Member;
  /** Applied to each field's wrapper — lets the caller control per-item width/layout. */
  itemClassName?: string;
}) {
  const { data: attributes } = useMemberAttributes();

  if (!attributes || attributes.length === 0) return null;

  return (
    <>
      {attributes.map((attribute) => (
        <Field
          key={attribute.id}
          label={attribute.label}
          htmlFor={`custom-${attribute.key}`}
          hint="optional"
          className={itemClassName}
        >
          <input type="hidden" name="custom_keys" value={attribute.key} />
          <AttributeInput attribute={attribute} member={member} />
        </Field>
      ))}
    </>
  );
}

function AttributeInput({
  attribute,
  member,
}: {
  attribute: MemberAttribute;
  member?: Member;
}) {
  // On edit, show what's stored (blank when there's nothing). Only the create
  // form prefills the definition's default — prefilling it on edit would write
  // the current default onto a member who never had a value, just because
  // someone opened the dialog, silently detaching them from later default changes.
  const value: CustomAttributeValue | undefined = member
    ? member.customAttributes?.[attribute.key]
    : attribute.defaultValue;

  const id = `custom-${attribute.key}`;
  const name = `custom_${attribute.key}`;

  switch (attribute.type) {
    case "boolean":
      return (
        <Checkbox
          id={id}
          name={name}
          label="Yes"
          value="true"
          defaultChecked={value === true}
        />
      );

    case "number":
      return (
        <Input
          id={id}
          name={name}
          type="number"
          step="any"
          defaultValue={value === null || value === undefined ? "" : String(value)}
        />
      );

    case "date":
      return (
        <Input
          id={id}
          name={name}
          type="date"
          defaultValue={typeof value === "string" ? value : ""}
        />
      );

    case "select":
      return (
        <Select
          id={id}
          name={name}
          defaultValue={typeof value === "string" ? value : ""}
        >
          <option value="">—</option>
          {(attribute.options ?? []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </Select>
      );

    default:
      return (
        <Input
          id={id}
          name={name}
          defaultValue={typeof value === "string" ? value : ""}
        />
      );
  }
}
