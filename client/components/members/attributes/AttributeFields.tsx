"use client";

import { useState } from "react";

import {
  ATTRIBUTE_TYPES,
  ATTRIBUTE_TYPE_LABELS,
  previewKey,
} from "@/lib/custom-attributes";
import type {
  CustomAttributeValue,
  MemberAttribute,
  MemberAttributeType,
} from "@/lib/types";
import { Checkbox, Field, Input, Select } from "@/components/ui/Field";
import { TagsInput } from "@/components/ui/TagsInput";

/**
 * Shared form fields for creating and editing a custom member attribute.
 *
 * Needs local state because two fields depend on the selected type: the options
 * list (dropdowns only) and the control used for the default value.
 */
export function AttributeFields({ attribute }: { attribute?: MemberAttribute }) {
  const isEdit = attribute !== undefined;
  const [type, setType] = useState<MemberAttributeType>(attribute?.type ?? "text");
  const [label, setLabel] = useState(attribute?.label ?? "");
  const [options, setOptions] = useState<string[]>(attribute?.options ?? []);

  const key = isEdit ? attribute.key : previewKey(label);

  return (
    <>
      <Field
        label="Name"
        htmlFor="attribute-label"
        help={
          key
            ? `Internal key: ${key}${isEdit ? " (can't be changed)" : ""}`
            : undefined
        }
      >
        <Input
          id="attribute-label"
          name="label"
          placeholder="Favourite colour"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          required
        />
      </Field>

      <Field
        label="Type"
        htmlFor="attribute-type"
        help={isEdit ? "Type can't be changed after creation." : undefined}
      >
        {/* The API rejects a type change outright - every stored value would
            become invalid - so on edit the picker is disabled and the current
            type rides along as a hidden input, purely so the default value and
            options can still be interpreted correctly on submit. */}
        <Select
          id="attribute-type"
          name={isEdit ? undefined : "type"}
          value={type}
          onChange={(e) => setType(e.target.value as MemberAttributeType)}
          disabled={isEdit}
        >
          {ATTRIBUTE_TYPES.map((t) => (
            <option key={t} value={t}>
              {ATTRIBUTE_TYPE_LABELS[t]}
            </option>
          ))}
        </Select>
        {isEdit && <input type="hidden" name="type" value={type} />}
      </Field>

      {type === "select" && (
        <Field
          label="Options"
          htmlFor="attribute-options"
          help="Press Enter or comma to add each choice."
        >
          {/* onChange keeps `options` in sync so the default-value picker below
              can offer the choices as they're typed. */}
          <TagsInput
            id="attribute-options"
            name="options"
            defaultValue={attribute?.options ?? []}
            placeholder="red, green, blue"
            onChange={setOptions}
          />
        </Field>
      )}

      <Field
        label="Default value"
        hint="optional"
        htmlFor="attribute-default"
        help={
          isEdit
            ? "Applies to members created from now on; existing members keep their values."
            : "Applied to every existing member as soon as you create this attribute."
        }
      >
        <DefaultValueInput
          type={type}
          options={options}
          current={attribute?.defaultValue}
        />
      </Field>
    </>
  );
}

/** Module-level so it keeps its identity across re-renders of the parent (the
 *  Name field is controlled, so it re-renders on every keystroke - a nested
 *  component would be remounted each time and lose whatever was typed here). */
function DefaultValueInput({
  type,
  options,
  current,
}: {
  type: MemberAttributeType;
  options: string[];
  current?: CustomAttributeValue;
}) {
  const asString = current === null || current === undefined ? "" : String(current);
  const id = "attribute-default";
  const name = "default_value";

  switch (type) {
    case "boolean":
      return (
        <Checkbox
          id={id}
          name={name}
          label="Yes"
          value="true"
          defaultChecked={current === true}
        />
      );
    case "number":
      return (
        <Input id={id} name={name} type="number" step="any" defaultValue={asString} />
      );
    case "date":
      return <Input id={id} name={name} type="date" defaultValue={asString} />;
    case "select":
      return (
        <Select id={id} name={name} defaultValue={asString}>
          <option value="">No default</option>
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </Select>
      );
    default:
      return <Input id={id} name={name} defaultValue={asString} />;
  }
}
