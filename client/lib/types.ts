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
  min_points: number;
  multiplier: number;
}

export interface Member {
  id: UUID;
  name: string;
  email: string;
  phone: string | null;
  segments: string[];
  /** Serialized by the API as `pointsBalance` (aliased from `total_points`). */
  pointsBalance: number;
}

export interface PointsTransaction {
  id: UUID;
  member_id: UUID;
  points: number;
  type: TransactionType;
  description: string | null;
  created_at: string;
}

export interface Balance {
  member_id: UUID;
  pointsBalance: number;
}

/** Dashboard aggregates from `GET /members/stats`. `by_tier` maps a tier id to
 * its member count; `untiered` counts members below the lowest tier. */
export interface MemberStats {
  count: number;
  points_in_circulation: number;
  by_tier: Record<string, number>;
  untiered: number;
}

export interface Reward {
  id: UUID;
  name: string;
  description: string | null;
  points_cost: number;
  /** `null` means unlimited stock. */
  stock: number | null;
  is_active: boolean;
  created_at: string;
}

export interface Redemption {
  id: UUID;
  member_id: UUID;
  reward_id: UUID;
  points_spent: number;
  source: RedemptionSource;
  reward: Reward;
  created_at: string;
}

export interface Challenge {
  id: UUID;
  name: string;
  description: string | null;
  target_value: number;
  reward_points: number;
  reward_id: UUID | null;
  is_active: boolean;
  starts_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface ChallengeAssignment {
  id: UUID;
  challenge_id: UUID;
  member_id: UUID;
  status: ChallengeStatus;
  current_value: number;
  assigned_at: string;
  completed_at: string | null;
  challenge: Challenge;
}

export interface ChallengeProgress {
  id: UUID;
  name: string;
  description: string | null;
  target_value: number;
  reward_points: number;
  reward_id: UUID | null;
  is_active: boolean;
  starts_at: string | null;
  expires_at: string | null;
  is_assigned: boolean;
  assignment_id: UUID | null;
  current_value: number;
  progress_percent: number;
  remaining: number;
  is_expired: boolean;
  effective_status: ChallengeStatus | null;
  assigned_at: string | null;
  completed_at: string | null;
}

export interface SegmentAssignResult {
  challenge_id: UUID;
  segment: string;
  assigned: number;
  skipped: number;
}
