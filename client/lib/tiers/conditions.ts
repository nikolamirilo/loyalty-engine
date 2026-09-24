/**
 * The tier condition language as the console shows it: which fields a
 * tier's conditions can test. The condition mini-language itself (operators,
 * value formatting) is shared with the event rule builder and lives in
 * `@/lib/conditions`.
 *
 * Fields mirror the API (`api/app/services/rules/fields.py:tier_fields`),
 * which validates every tier's conditions again on save. Unlike an event
 * rule's fields, there is no `member.tier` here: a tier can't be defined in
 * terms of the tier it is itself deciding.
 */

import { attributeField, CUSTOM_PREFIX, named, type FieldDef } from "@/lib/conditions";
import type { MemberAttribute, Segment } from "@/lib/types";

/** Program data the tier builder picks from. */
export interface TierCatalog {
  segments: Segment[];
  memberAttributes: MemberAttribute[];
}

export const PURCHASE_SPEND_FIELD = "member.purchaseSpendCents";
export const PURCHASE_COUNT_FIELD = "member.purchaseCount";

/** Everything a tier's conditions can test. */
export function tierConditionFields(catalog: TierCatalog): FieldDef[] {
  return [
    { value: "member.pointsBalance", label: "Points balance", group: "member", kind: "number" },
    { value: PURCHASE_SPEND_FIELD, label: "Lifetime purchase spend (cents)", group: "member", kind: "number" },
    { value: PURCHASE_COUNT_FIELD, label: "Lifetime purchase count", group: "member", kind: "number" },
    { value: "member.segments", label: "Segments", group: "member", kind: "segments", options: named(catalog.segments) },
    ...catalog.memberAttributes.map((a) => attributeField(CUSTOM_PREFIX, "member", a)),
  ];
}
