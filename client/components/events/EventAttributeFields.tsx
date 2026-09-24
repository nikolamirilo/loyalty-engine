"use client";

import type { EventAttribute } from "@/lib/types";
import { Field, Input, Select } from "@/components/ui/Field";

/**
 * One form field per event attribute, named `attr.<key>` so `sendEvent` can
 * read them straight off `FormData`. Shared by every place an
 * admin fills in an event by hand: a member's page, a single event's page,
 * and the events list.
 */
export function EventAttributeFields({ attributes }: { attributes: EventAttribute[] }) {
  return (
    <>
      {attributes.map((attribute) => (
        <Field key={attribute.key} label={attribute.label} htmlFor={`attr-${attribute.key}`} hint="optional">
          <AttributeInput attribute={attribute} />
        </Field>
      ))}
    </>
  );
}

function AttributeInput({ attribute }: { attribute: EventAttribute }) {
  const name = `attr.${attribute.key}`;
  const id = `attr-${attribute.key}`;
  if (attribute.type === "select" || attribute.type === "boolean") {
    const options =
      attribute.type === "boolean"
        ? [
            { value: "true", label: "Yes" },
            { value: "false", label: "No" },
          ]
        : (attribute.options ?? []).map((o) => ({ value: o, label: o }));
    return (
      <Select id={id} name={name} defaultValue="">
        <option value="">Not sent</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </Select>
    );
  }
  return (
    <Input
      id={id}
      name={name}
      type={attribute.type === "number" ? "number" : attribute.type === "date" ? "date" : "text"}
      step={attribute.type === "number" ? "any" : undefined}
    />
  );
}
