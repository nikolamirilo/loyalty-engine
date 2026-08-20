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

/** Mirrors `slugify()` in api/app/services/custom_attributes.py, so the Configure
 *  form can preview the camelCase internal key the server will derive from a
 *  label. Kept in sync by hand — it's only a preview; the server's value is
 *  authoritative. */
export function previewKey(label: string): string {
  const words = label.match(/[A-Za-z0-9]+/g) ?? [];
  if (words.length === 0) return "";
  return (
    words[0].toLowerCase() +
    words
      .slice(1)
      .map((w) => w[0].toUpperCase() + w.slice(1).toLowerCase())
      .join("")
  ).slice(0, 63);
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
