/**
 * The condition mini-language, shared by the event rule builder
 * (`components/events/rules.ts`) and the tier builder
 * (`lib/tiers/conditions.ts`): which fields a condition can test, which
 * operators fit each field, and how a condition reads as a sentence.
 *
 * Field paths and operators mirror the API
 * (`api/app/services/rules/conditions.py`), which validates every condition
 * again on save. This module only drives the two builders.
 */

import type {
  EventAttribute,
  MemberAttributeType,
  RuleCondition,
  RuleOperator,
  RuleValue,
} from "@/lib/types";

export const CUSTOM_PREFIX = "member.customAttributes.";

// ── fields ───────────────────────────────────────────────────────────────────

export type FieldKind = MemberAttributeType | "segments" | "tier";

export interface FieldOption {
  value: string;
  label: string;
}

export interface FieldDef {
  value: string;
  label: string;
  group: "event" | "member";
  kind: FieldKind;
  options?: FieldOption[];
}

export const BOOLEAN_OPTIONS: FieldOption[] = [
  { value: "true", label: "Yes" },
  { value: "false", label: "No" },
];

/** A condition field for one admin-defined attribute (an event attribute or a
 *  member custom attribute - both share this shape). */
export function attributeField(
  prefix: string,
  group: FieldDef["group"],
  attribute: Pick<EventAttribute, "key" | "label" | "type" | "options">,
): FieldDef {
  const options =
    attribute.type === "select"
      ? (attribute.options ?? []).map((o) => ({ value: o, label: o }))
      : attribute.type === "boolean"
        ? BOOLEAN_OPTIONS
        : undefined;
  return {
    value: `${prefix}${attribute.key}`,
    label: attribute.label,
    group,
    kind: attribute.type,
    options,
  };
}

export const named = (items: { id: string; name: string }[]) =>
  items.map((i) => ({ value: i.id, label: i.name }));

// ── operators ────────────────────────────────────────────────────────────────

const OPERATORS: Record<FieldKind, RuleOperator[]> = {
  number: ["gte", "gt", "eq", "neq", "lte", "lt"],
  text: ["eq", "neq", "contains"],
  select: ["eq", "neq"],
  boolean: ["eq"],
  date: ["lt", "gt", "eq"],
  segments: ["contains"],
  tier: ["eq", "neq"],
};

const OPERATOR_LABELS: Record<RuleOperator, string> = {
  eq: "is",
  neq: "is not",
  gt: "is more than",
  gte: "is at least",
  lt: "is less than",
  lte: "is at most",
  contains: "contains",
};

const DATE_OPERATOR_LABELS: Partial<Record<RuleOperator, string>> = {
  lt: "is before",
  gt: "is after",
  eq: "is on",
};

export function operatorsFor(field: FieldDef): RuleOperator[] {
  return OPERATORS[field.kind];
}

export function operatorLabel(field: FieldDef, operator: RuleOperator): string {
  if (field.kind === "date") return DATE_OPERATOR_LABELS[operator] ?? OPERATOR_LABELS[operator];
  if (field.kind === "segments") return "include";
  return OPERATOR_LABELS[operator];
}

// ── values ───────────────────────────────────────────────────────────────────

/** A value as a builder's inputs hold it. */
export function valueToInput(value: RuleValue): string {
  return value === null ? "" : String(value);
}

/** A fresh condition on `field`: its first operator and first option. */
export function conditionFor(field: FieldDef): RuleCondition {
  return {
    field: field.value,
    operator: operatorsFor(field)[0],
    value: field.options?.[0]?.value ?? "",
  };
}

// ── sentences ────────────────────────────────────────────────────────────────

export const lowerFirst = (s: string) => s.charAt(0).toLowerCase() + s.slice(1);

export function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function subject(field: FieldDef): string {
  return field.group === "member" ? `member's ${lowerFirst(field.label)}` : lowerFirst(field.label);
}

export function valueLabel(field: FieldDef | undefined, value: RuleValue): string {
  const raw = valueToInput(value);
  return field?.options?.find((o) => o.value === raw)?.label ?? (raw || "…");
}

export function conditionText(condition: RuleCondition, fields: FieldDef[]): string {
  const field = fields.find((f) => f.value === condition.field);
  if (!field) return "Unknown field";
  return `${subject(field)} ${operatorLabel(field, condition.operator)} ${valueLabel(field, condition.value)}`;
}
