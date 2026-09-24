/**
 * The event rule language as the console shows it: which fields a condition
 * can test, which member fields a rule can set, and how a rule reads as a
 * sentence. The condition mini-language itself (fields, operators, value
 * formatting) is shared with the tier builder and lives in `@/lib/conditions`.
 *
 * Field paths and operators mirror the API (api/app/services/rules), which
 * validates every rule again on save. This module only drives the builder.
 */

import {
  attributeField,
  conditionText,
  CUSTOM_PREFIX,
  lowerFirst,
  named,
  subject,
  valueLabel,
  type FieldDef,
} from "@/lib/conditions";
import type {
  Challenge,
  EventAttribute,
  EventRule,
  EventType,
  MemberAttribute,
  Reward,
  RuleEffect,
  RuleEffectType,
  Segment,
  Tier,
} from "@/lib/types";

export {
  capitalize,
  conditionFor,
  conditionText,
  operatorLabel,
  operatorsFor,
  valueToInput,
} from "@/lib/conditions";
export type { FieldDef, FieldOption } from "@/lib/conditions";

export const EVENT_PREFIX = "event.attributes.";

/** Program data the rule builder picks from. */
export interface Catalog {
  rewards: Reward[];
  challenges: Challenge[];
  segments: Segment[];
  tiers: Tier[];
  memberAttributes: MemberAttribute[];
}

// ── fields ───────────────────────────────────────────────────────────────────

/** Everything a condition on `eventType` can test, event attributes first. */
export function conditionFields(eventType: EventType, catalog: Catalog): FieldDef[] {
  return [
    ...eventType.attributes.map((a) => attributeField(EVENT_PREFIX, "event", a)),
    { value: "member.pointsBalance", label: "Points balance", group: "member", kind: "number" },
    { value: "member.tier", label: "Tier", group: "member", kind: "tier", options: named(catalog.tiers) },
    { value: "member.segments", label: "Segments", group: "member", kind: "segments", options: named(catalog.segments) },
    ...catalog.memberAttributes.map((a) => attributeField(CUSTOM_PREFIX, "member", a)),
  ];
}

/** Member fields an "Update member" effect can set. Email is left out: it is
 *  unique across programs and tied to verification. */
export function updatableFields(catalog: Catalog): FieldDef[] {
  return [
    { value: "member.name", label: "Name", group: "member", kind: "text" },
    { value: "member.phone", label: "Phone", group: "member", kind: "text" },
    ...catalog.memberAttributes.map((a) => attributeField(CUSTOM_PREFIX, "member", a)),
  ];
}

/** Event attributes whose value can be copied into `target`: the same type,
 *  or anything when the target is plain text. */
export function copyableAttributes(eventType: EventType, target: FieldDef): EventAttribute[] {
  return eventType.attributes.filter((a) => target.kind === "text" || a.type === target.kind);
}

// ── effects ──────────────────────────────────────────────────────────────────

export const EFFECT_TYPES: { value: RuleEffectType; label: string }[] = [
  { value: "addPoints", label: "Earn points" },
  { value: "burnPoints", label: "Burn points" },
  { value: "grantReward", label: "Give a reward" },
  { value: "assignChallenge", label: "Assign challenge" },
  { value: "addChallengeProgress", label: "Add challenge progress" },
  { value: "addToSegment", label: "Add to segment" },
  { value: "removeFromSegment", label: "Remove from segment" },
  { value: "updateMember", label: "Update member" },
];

// ── sentences ────────────────────────────────────────────────────────────────

const nameOf = (items: { id: string; name: string }[], id: string) =>
  items.find((i) => i.id === id)?.name ?? "…";

export function effectText(effect: RuleEffect, eventType: EventType, catalog: Catalog): string {
  const attributeLabel = (key: string | null) =>
    lowerFirst(eventType.attributes.find((a) => a.key === key)?.label ?? "…");

  switch (effect.type) {
    case "addPoints":
    case "burnPoints": {
      const verb = effect.type === "addPoints" ? "earn" : "burn";
      if (effect.fromAttribute) return `${verb} points equal to the event's ${attributeLabel(effect.fromAttribute)}`;
      return `${verb} ${effect.points ?? "…"} ${effect.points === 1 ? "point" : "points"}`;
    }
    case "grantReward":
      return `give reward "${nameOf(catalog.rewards, effect.rewardId)}"`;
    case "assignChallenge":
      return `assign challenge "${nameOf(catalog.challenges, effect.challengeId)}"`;
    case "addChallengeProgress": {
      const challenge = nameOf(catalog.challenges, effect.challengeId);
      if (effect.fromAttribute)
        return `add progress to "${challenge}" equal to the event's ${attributeLabel(effect.fromAttribute)}`;
      return `add ${effect.amount ?? 1} progress to "${challenge}"`;
    }
    case "addToSegment":
      return `add member to segment "${nameOf(catalog.segments, effect.segmentId)}"`;
    case "removeFromSegment":
      return `remove member from segment "${nameOf(catalog.segments, effect.segmentId)}"`;
    case "updateMember": {
      const fields = updatableFields(catalog);
      const parts = effect.fields.map((update) => {
        const field = fields.find((f) => f.value === update.field);
        const target = field ? subject(field) : update.field;
        if (update.fromAttribute) return `${target} to the event's ${attributeLabel(update.fromAttribute)}`;
        return update.value === null || update.value === ""
          ? `${target} to empty`
          : `${target} to ${valueLabel(field, update.value)}`;
      });
      return `set ${parts.join(", ") || "…"}`;
    }
  }
}

/** The whole rule in plain words, e.g. for the editor's live preview. */
export function ruleSentence(
  rule: Pick<EventRule, "conditions" | "effects" | "limitPerMember">,
  eventType: EventType,
  catalog: Catalog,
): string {
  const fields = conditionFields(eventType, catalog);
  const conditions = rule.conditions.map((c) => conditionText(c, fields));
  const effects = rule.effects.map((e) => effectText(e, eventType, catalog));
  const ifPart = conditions.length ? `, if ${conditions.join(" and ")}` : "";
  const thenPart = `${conditions.length ? ", then " : ", "}${effects.join(" and ") || "…"}`;
  const limit = rule.limitPerMember === 1 ? ", only the first time per member" : "";
  return `When "${eventType.name}" happens${ifPart}${thenPart}${limit}.`;
}

// ── integration example ──────────────────────────────────────────────────────

/** A believable text value when the label says what it holds ("Email",
 *  "E-mail", "Customer email"), otherwise a placeholder like "<store name>".
 *  Matching ignores case, spaces and punctuation. Names match only when the
 *  whole label is a person's name, so "Store name" stays a placeholder. */
function sampleText(label: string): string {
  const compact = label.toLowerCase().replace(/[^a-z0-9]/g, "");
  if (compact.includes("email")) return "member@example.com";
  if (compact.includes("phone")) return "+41 79 123 45 67";
  if (compact === "name" || compact === "fullname") return "Ada Lovelace";
  if (compact === "firstname") return "Ada";
  if (compact === "lastname") return "Lovelace";
  if (["url", "link", "website"].some((word) => compact.includes(word))) return "https://example.com";
  return `<${label.toLowerCase()}>`;
}

function sampleValue(attribute: EventAttribute): unknown {
  switch (attribute.type) {
    case "number":
      return 45;
    case "boolean":
      return false;
    case "date":
      return "2026-10-01";
    case "select":
      return attribute.options?.[0] ?? "";
    default:
      return sampleText(attribute.label);
  }
}

/** The request an integrator sends for `eventType`. */
export function curlExample(eventType: EventType): string {
  const body = {
    memberId: "<member id>",
    type: eventType.key,
    attributes: Object.fromEntries(eventType.attributes.map((a) => [a.key, sampleValue(a)])),
    eventId: "<your id for this event, optional>",
  };
  const json = JSON.stringify(body, null, 2)
    .split("\n")
    .map((line, i) => (i === 0 ? line : `  ${line}`))
    .join("\n");
  return [
    "curl -X POST $API_URL/events \\",
    '  -H "Authorization: Bearer $API_TOKEN" \\',
    '  -H "X-Program-Id: <program id>" \\',
    '  -H "Content-Type: application/json" \\',
    `  -d '${json}'`,
  ].join("\n");
}
