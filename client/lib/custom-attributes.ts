import type {
  CustomAttributeValue,
  MemberAttribute,
  MemberAttributeType,
} from "@/lib/types";

/** Human labels for the attribute types, shared by the Configure table and the
 *  type picker so the two can't drift. */
export const ATTRIBUTE_TYPE_LABELS: Record<MemberAttributeType, string> = {
  text: "Text",
  number: "Number",
  boolean: "Yes / No",
  date: "Date",
  select: "Dropdown",
};

export const ATTRIBUTE_TYPES = Object.keys(
  ATTRIBUTE_TYPE_LABELS,
) as MemberAttributeType[];

/** Mirrors `slugify()` in api/custom_attributes.py, so the Configure form can
 *  preview the internal key the server will derive from a label. Kept in sync by
 *  hand — it's only a preview; the server's value is authoritative. */
export function previewKey(label: string): string {
  return label
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 63)
    .replace(/^_+|_+$/g, "");
}

/** Render a stored value for read-only display. */
export function formatCustomValue(
  attribute: MemberAttribute,
  value: CustomAttributeValue | undefined,
): string | null {
  if (value === undefined || value === null || value === "") return null;
  if (attribute.type === "boolean") return value ? "Yes" : "No";
  if (attribute.type === "number") return String(value);
  return String(value);
}
