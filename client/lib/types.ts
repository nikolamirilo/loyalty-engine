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

export interface Tier {
  id: UUID;
  name: string;
  minPoints: number;
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
  name: string;
  email: string;
  phone: string | null;
  segments: SegmentSummary[];
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
