// Types mirroring the FastAPI response schemas (server/schemas.py).

export type UUID = string;

export type TransactionType = "earn" | "spend" | "adjust";
export type RedemptionSource = "redeemed" | "assigned";
export type ChallengeStatus =
  | "assigned"
  | "in_progress"
  | "completed"
  | "expired"
  | "cancelled";

/**
 * One isolated dataset: its own rewards, products, challenges, tiers, segments
 * and members. Every API call carries the selected program in an
 * `X-Program-Id` header, so nothing below ever crosses between two of them.
 */
export interface Program {
  id: UUID;
  name: string;
  slug: string;
  description: string | null;
  isDefault: boolean;
  /** Public URL in the Supabase Storage bucket, or null for the stock logo.
   *  Only ever set through the logo upload, never in a create/update body. */
  logoUrl: string | null;
  /** "#rrggbb", or null for the stock theme. Drives buttons, links, the
   *  active nav item and every other `primary` token (see lib/theme.ts). */
  primaryColor: string | null;
  /** "#rrggbb", or null. The accent end of the member app's tier banner. */
  secondaryColor: string | null;
  createdAt: string;
}

/**
 * A program as seen by one person: `memberId` is their membership in it, or
 * null when they have not joined it yet.
 */
export interface MemberProgram extends Program {
  memberId: UUID | null;
}

export interface Tier {
  id: UUID;
  name: string;
  /** Tiers are tried highest rank first; a member is assigned to the first
   *  whose conditions all match. Ties break by creation order. */
  rank: number;
  /** All must match - the same rule an event rule's conditions follow. No
   *  conditions matches every member, so a tier with none is a catch-all
   *  wherever it sits in the rank order (typically the lowest). */
  conditions: RuleCondition[];
  multiplier: number;
}

/** Minimal segment shape embedded in a member (see `Segment` for the full object). */
export interface SegmentSummary {
  id: UUID;
  name: string;
  description: string | null;
  color: string | null;
}

export interface Segment extends SegmentSummary {
  createdAt: string;
  memberCount: number;
}

export type MemberAttributeType =
  | "text"
  | "number"
  | "boolean"
  | "date"
  | "select";

export type CustomAttributeValue = string | number | boolean | null;

/** An admin-defined custom field on members, from `GET /member-attributes`.
 *
 * `key` and `type` are immutable server-side: renaming the key would orphan
 * every stored value and changing the type would invalidate them. `label` and
 * `defaultValue` stay editable. */
export interface MemberAttribute {
  id: UUID;
  key: string;
  label: string;
  type: MemberAttributeType;
  /** Choice list for `select`; null for every other type. */
  options: string[] | null;
  defaultValue: CustomAttributeValue;
  createdAt: string;
}

export interface Member {
  id: UUID;
  /** The program this membership belongs to. The id above is only addressable
   * from within it, so the two always travel together. */
  programId: UUID;
  name: string;
  email: string;
  phone: string | null;
  segments: SegmentSummary[];
  /** The tier the API last assigned (`apply_tier`), or null when the member
   * doesn't meet any tier's conditions / no tiers are defined. A tier's
   * conditions can reach beyond the points balance, so this is the only
   * correct source - there is no client-side way to recompute it. */
  tier: Tier | null;
  /** Serialized by the API as `pointsBalance` (aliased from `total_points`). */
  pointsBalance: number;
  /** Values for the fields defined in `MemberAttribute`, keyed by their `key`.
   * A key can be absent — the UI renders from the definitions list, so absent
   * and null both display as empty. Serialized by the API as `customAttributes`. */
  customAttributes: Record<string, CustomAttributeValue>;
  /** Set by the DOI email-verification flow (or an admin override); null = unverified.
   * Serialized by the API as `emailVerifiedAt`. */
  emailVerifiedAt: string | null;
  /** Computed as `emailVerifiedAt !== null` - convenience mirror of that field.
   * Serialized by the API as `isEmailVerified`. */
  isEmailVerified: boolean;
}

export interface PointsTransaction {
  id: UUID;
  memberId: UUID;
  points: number;
  type: TransactionType;
  description: string | null;
  createdAt: string;
}

export interface Balance {
  memberId: UUID;
  pointsBalance: number;
}

/** Dashboard aggregates from `GET /members/stats`. `byTier` maps a tier id to
 * its member count; `untiered` counts members below the lowest tier. */
export interface MemberStats {
  count: number;
  pointsInCirculation: number;
  byTier: Record<string, number>;
  untiered: number;
}

export interface Reward {
  id: UUID;
  name: string;
  description: string | null;
  pointsCost: number;
  segments: string[];
  /** `null` means unlimited stock. */
  stock: number | null;
  isActive: boolean;
  createdAt: string;
}

export interface Product {
  id: UUID;
  name: string;
  description: string | null;
  priceCents: number;
  currency: string;
  category: string | null;
  isActive: boolean;
  createdAt: string;
}

export interface Purchase {
  id: UUID;
  memberId: UUID;
  /** Null if the product was later deleted; `productName` still holds. */
  productId: UUID | null;
  productName: string;
  quantity: number;
  unitPriceCents: number;
  totalCents: number;
  currency: string;
  createdAt: string;
}

/** Spend and frequency signals for one member, from
 * `GET /members/{id}/purchase-stats?days=`. `period*` covers the trailing
 * `periodDays` window; the rest are lifetime totals. This is the input
 * gamification campaigns personalise on. */
export interface PurchaseStats {
  memberId: UUID;
  currency: string;
  purchaseCount: number;
  totalSpendCents: number;
  averageOrderValueCents: number;
  firstPurchaseAt: string | null;
  lastPurchaseAt: string | null;
  daysSinceLastPurchase: number | null;
  periodDays: number;
  periodPurchaseCount: number;
  periodSpendCents: number;
}

export interface Redemption {
  id: UUID;
  memberId: UUID;
  rewardId: UUID;
  pointsSpent: number;
  source: RedemptionSource;
  reward: Reward;
  createdAt: string;
}

export interface Challenge {
  id: UUID;
  name: string;
  description: string | null;
  targetValue: number;
  rewardPoints: number;
  rewardId: UUID | null;
  isActive: boolean;
  startsAt: string | null;
  expiresAt: string | null;
  /** Expires this many days after a member is assigned, instead of the fixed
   * `expiresAt` date above. Null means "use `expiresAt` for everyone". */
  expiryDays: number | null;
  createdAt: string;
  /** Segments this challenge has been bulk-assigned to (via "Assign to segment"). */
  segments: string[];
}

export interface ChallengeAssignment {
  id: UUID;
  challengeId: UUID;
  memberId: UUID;
  status: ChallengeStatus;
  currentValue: number;
  assignedAt: string;
  /** This member's personal deadline - distinct from `challenge.expiresAt`. */
  expiresAt: string | null;
  completedAt: string | null;
  challenge: Challenge;
}

export interface ChallengeProgress {
  id: UUID;
  name: string;
  description: string | null;
  targetValue: number;
  rewardPoints: number;
  rewardId: UUID | null;
  isActive: boolean;
  startsAt: string | null;
  expiresAt: string | null;
  isAssigned: boolean;
  assignmentId: UUID | null;
  currentValue: number;
  progressPercent: number;
  remaining: number;
  isExpired: boolean;
  effectiveStatus: ChallengeStatus | null;
  assignedAt: string | null;
  completedAt: string | null;
}

export interface SegmentAssignResult {
  challengeId: UUID;
  segmentId: UUID;
  assigned: number;
  skipped: number;
}

// ── Events and rules ─────────────────────────────────────────────────────────

/** One attribute of an event type: data the sending system includes. */
export interface EventAttribute {
  key: string;
  label: string;
  type: MemberAttributeType;
  options: string[] | null;
}

export type RuleOperator = "eq" | "neq" | "gt" | "gte" | "lt" | "lte" | "contains";

export type RuleValue = string | number | boolean | null;

/** `field` is a path: `event.attributes.<key>`, `member.pointsBalance`,
 *  `member.tier`, `member.segments` or `member.customAttributes.<key>`. */
export interface RuleCondition {
  field: string;
  operator: RuleOperator;
  value: RuleValue;
}

/** One member field an `updateMember` effect sets: to `value`, or to a copy of
 *  the event attribute named in `fromAttribute`. */
export interface MemberFieldUpdate {
  field: string;
  value: RuleValue;
  fromAttribute: string | null;
}

export type RuleEffect =
  // Numbers are fixed, or read from the event attribute named in fromAttribute.
  | { type: "addPoints"; points: number | null; fromAttribute: string | null }
  | { type: "burnPoints"; points: number | null; fromAttribute: string | null }
  | { type: "grantReward"; rewardId: UUID }
  | { type: "assignChallenge"; challengeId: UUID }
  | { type: "addChallengeProgress"; challengeId: UUID; amount: number | null; fromAttribute: string | null }
  | { type: "addToSegment"; segmentId: UUID }
  | { type: "removeFromSegment"; segmentId: UUID }
  | { type: "updateMember"; fields: MemberFieldUpdate[] };

export type RuleEffectType = RuleEffect["type"];

export interface EventRule {
  id: UUID;
  eventTypeId: UUID;
  name: string;
  isActive: boolean;
  conditions: RuleCondition[];
  effects: RuleEffect[];
  /** How many times one member can trigger the rule. Null means every time. */
  limitPerMember: number | null;
  createdAt: string;
}

/** Something a member does that an outside system reports, from `GET /event-types`. */
export interface EventType {
  id: UUID;
  /** What callers send as the event `type`. Fixed once created. */
  key: string;
  name: string;
  description: string | null;
  isActive: boolean;
  attributes: EventAttribute[];
  rules: EventRule[];
  createdAt: string;
}

/** Body for creating or editing an event type. Send `key` only to keep an
 *  existing attribute; new ones get a key derived from their label. */
export interface EventTypeInput {
  name: string;
  description: string | null;
  /** Omit to leave it as is. It's switched on the event's own page. */
  isActive?: boolean;
  attributes: { key?: string; label: string; type: MemberAttributeType; options: string[] | null }[];
}

export interface EventRuleInput {
  name: string;
  isActive: boolean;
  conditions: RuleCondition[];
  effects: RuleEffect[];
  limitPerMember: number | null;
}

/** What one effect of a matching rule did (or why it was skipped). */
export interface AppliedEffect {
  ruleId: UUID;
  ruleName: string;
  type: string;
  summary: string;
  skipped: boolean;
  points: number | null;
  rewardId: UUID | null;
}

/** One event received for a member, from `GET /members/{id}/events`. */
export interface MemberEvent {
  id: UUID;
  memberId: UUID;
  /** The event type's key. */
  type: string;
  /** The event type's name, or its key once the type is deleted. */
  name: string;
  attributes: Record<string, CustomAttributeValue>;
  effects: AppliedEffect[];
  /** The sender's own id for the event, if it gave one. */
  eventId: string | null;
  createdAt: string;
}

/** An event in the program-wide log, with the member it was for. */
export interface EventLogEntry extends MemberEvent {
  member: { id: UUID; name: string; email: string };
}
