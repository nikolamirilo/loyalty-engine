"use server";

import { revalidatePath } from "next/cache";

import type { ActionState } from "./action-state";
import { ApiError, apiRequest } from "./api";

function fail(error: unknown): ActionState {
  if (error instanceof ApiError) return { ok: false, error: error.message };
  return { ok: false, error: "Something went wrong. Please try again." };
}

// ── form-data helpers ────────────────────────────────────────────────────────

function str(fd: FormData, key: string): string {
  const v = fd.get(key);
  return typeof v === "string" ? v.trim() : "";
}

function optionalStr(fd: FormData, key: string): string | null {
  const v = str(fd, key);
  return v === "" ? null : v;
}

function parseNumber(fd: FormData, key: string): number | null {
  const v = str(fd, key);
  if (v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function parseSegmentIds(fd: FormData): string[] {
  return fd
    .getAll("segment_ids")
    .map((s) => (typeof s === "string" ? s.trim() : ""))
    .filter(Boolean);
}

function checkbox(fd: FormData, key: string): boolean {
  return fd.get(key) != null;
}

function revalidateMember(id: string) {
  revalidatePath("/");
  revalidatePath("/members");
  revalidatePath(`/members/${id}`);
}

// ── Members ──────────────────────────────────────────────────────────────────

export async function createMember(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const name = str(fd, "name");
  const email = str(fd, "email");
  if (!name) return { ok: false, error: "Name is required." };
  if (!email) return { ok: false, error: "Email is required." };
  try {
    await apiRequest("/members", {
      method: "POST",
      json: {
        name,
        email,
        phone: optionalStr(fd, "phone"),
        segment_ids: parseSegmentIds(fd),
      },
    });
    revalidatePath("/");
    revalidatePath("/members");
    return { ok: true, message: "Member created." };
  } catch (e) {
    return fail(e);
  }
}

export async function updateMember(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = str(fd, "id");
  const name = str(fd, "name");
  const email = str(fd, "email");
  if (!id) return { ok: false, error: "Missing member id." };
  if (!name) return { ok: false, error: "Name is required." };
  if (!email) return { ok: false, error: "Email is required." };
  try {
    await apiRequest(`/members/${id}`, {
      method: "PATCH",
      json: {
        name,
        email,
        phone: optionalStr(fd, "phone"),
        segment_ids: parseSegmentIds(fd),
      },
    });
    revalidateMember(id);
    return { ok: true, message: "Member updated." };
  } catch (e) {
    return fail(e);
  }
}

export async function deleteMember(id: string): Promise<ActionState> {
  try {
    await apiRequest(`/members/${id}`, { method: "DELETE" });
    revalidatePath("/");
    revalidatePath("/members");
    return { ok: true, message: "Member deleted." };
  } catch (e) {
    return fail(e);
  }
}

// ── Points ───────────────────────────────────────────────────────────────────

export async function earnPoints(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = str(fd, "member_id");
  const points = parseNumber(fd, "points");
  if (!points || points <= 0)
    return { ok: false, error: "Enter a positive number of points." };
  try {
    await apiRequest(`/members/${id}/points/earn`, {
      method: "POST",
      json: { points, description: optionalStr(fd, "description") },
    });
    revalidateMember(id);
    return { ok: true, message: "Points earned." };
  } catch (e) {
    return fail(e);
  }
}

export async function burnPoints(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = str(fd, "member_id");
  const points = parseNumber(fd, "points");
  if (!points || points <= 0)
    return { ok: false, error: "Enter a positive number of points." };
  try {
    await apiRequest(`/members/${id}/points/burn`, {
      method: "POST",
      json: { points, description: optionalStr(fd, "description") },
    });
    revalidateMember(id);
    return { ok: true, message: "Points burned." };
  } catch (e) {
    return fail(e);
  }
}

export async function adjustPoints(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = str(fd, "member_id");
  const points = parseNumber(fd, "points");
  if (points === null || points === 0)
    return { ok: false, error: "Enter a non-zero adjustment (+ or -)." };
  try {
    await apiRequest(`/members/${id}/points/adjust`, {
      method: "POST",
      json: { points, description: optionalStr(fd, "description") },
    });
    revalidateMember(id);
    return { ok: true, message: "Balance adjusted." };
  } catch (e) {
    return fail(e);
  }
}

// ── Redemptions & prizes ─────────────────────────────────────────────────────

export async function redeemReward(
  memberId: string,
  rewardId: string,
): Promise<ActionState> {
  try {
    await apiRequest(`/members/${memberId}/redeem/${rewardId}`, {
      method: "POST",
    });
    revalidateMember(memberId);
    revalidatePath("/rewards");
    return { ok: true, message: "Reward redeemed." };
  } catch (e) {
    return fail(e);
  }
}

export async function assignPrize(
  memberId: string,
  rewardId: string,
): Promise<ActionState> {
  try {
    await apiRequest(`/members/${memberId}/prizes/${rewardId}`, {
      method: "POST",
    });
    revalidateMember(memberId);
    revalidatePath("/rewards");
    return { ok: true, message: "Prize assigned." };
  } catch (e) {
    return fail(e);
  }
}

// ── Rewards ──────────────────────────────────────────────────────────────────

function rewardBody(fd: FormData) {
  return {
    name: str(fd, "name"),
    description: optionalStr(fd, "description"),
    points_cost: parseNumber(fd, "points_cost"),
    stock: parseNumber(fd, "stock"), // null => unlimited
    is_active: checkbox(fd, "is_active"),
  };
}

export async function createReward(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const body = rewardBody(fd);
  if (!body.name) return { ok: false, error: "Name is required." };
  if (!body.points_cost || body.points_cost <= 0)
    return { ok: false, error: "Points cost must be greater than 0." };
  try {
    await apiRequest("/rewards", { method: "POST", json: body });
    revalidatePath("/");
    revalidatePath("/rewards");
    return { ok: true, message: "Reward created." };
  } catch (e) {
    return fail(e);
  }
}

export async function updateReward(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = str(fd, "id");
  const body = rewardBody(fd);
  if (!id) return { ok: false, error: "Missing reward id." };
  if (!body.name) return { ok: false, error: "Name is required." };
  if (!body.points_cost || body.points_cost <= 0)
    return { ok: false, error: "Points cost must be greater than 0." };
  try {
    await apiRequest(`/rewards/${id}`, { method: "PATCH", json: body });
    revalidatePath("/");
    revalidatePath("/rewards");
    return { ok: true, message: "Reward updated." };
  } catch (e) {
    return fail(e);
  }
}

export async function setRewardActive(
  id: string,
  isActive: boolean,
): Promise<ActionState> {
  try {
    await apiRequest(`/rewards/${id}`, {
      method: "PATCH",
      json: { is_active: isActive },
    });
    revalidatePath("/");
    revalidatePath("/rewards");
    return { ok: true };
  } catch (e) {
    return fail(e);
  }
}

export async function deleteReward(id: string): Promise<ActionState> {
  try {
    await apiRequest(`/rewards/${id}`, { method: "DELETE" });
    revalidatePath("/");
    revalidatePath("/rewards");
    return { ok: true, message: "Reward deleted." };
  } catch (e) {
    return fail(e);
  }
}

// ── Challenges ───────────────────────────────────────────────────────────────

function challengeBody(fd: FormData) {
  return {
    name: str(fd, "name"),
    description: optionalStr(fd, "description"),
    target_value: parseNumber(fd, "target_value"),
    reward_points: parseNumber(fd, "reward_points") ?? 0,
    reward_id: optionalStr(fd, "reward_id"),
    is_active: checkbox(fd, "is_active"),
    expires_at: toIso(optionalStr(fd, "expires_at")),
  };
}

/** `datetime-local` value ("2026-07-20T14:30") -> ISO string, or null. */
function toIso(value: string | null): string | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

export async function createChallenge(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const body = challengeBody(fd);
  if (!body.name) return { ok: false, error: "Name is required." };
  if (!body.target_value || body.target_value <= 0)
    return { ok: false, error: "Target value must be greater than 0." };
  try {
    await apiRequest("/challenges", { method: "POST", json: body });
    revalidatePath("/");
    revalidatePath("/challenges");
    return { ok: true, message: "Challenge created." };
  } catch (e) {
    return fail(e);
  }
}

export async function updateChallenge(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = str(fd, "id");
  const body = challengeBody(fd);
  if (!id) return { ok: false, error: "Missing challenge id." };
  if (!body.name) return { ok: false, error: "Name is required." };
  if (!body.target_value || body.target_value <= 0)
    return { ok: false, error: "Target value must be greater than 0." };
  try {
    await apiRequest(`/challenges/${id}`, { method: "PATCH", json: body });
    revalidatePath("/");
    revalidatePath("/challenges");
    return { ok: true, message: "Challenge updated." };
  } catch (e) {
    return fail(e);
  }
}

export async function deleteChallenge(id: string): Promise<ActionState> {
  try {
    await apiRequest(`/challenges/${id}`, { method: "DELETE" });
    revalidatePath("/");
    revalidatePath("/challenges");
    return { ok: true, message: "Challenge deleted." };
  } catch (e) {
    return fail(e);
  }
}

export async function assignChallengeToSegment(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = str(fd, "challenge_id");
  const segmentId = str(fd, "segment_id");
  if (!segmentId) return { ok: false, error: "Choose a segment." };
  try {
    const result = await apiRequest<{ assigned: number; skipped: number }>(
      `/challenges/${id}/assign-segment`,
      { method: "POST", json: { segment_id: segmentId } },
    );
    revalidatePath("/");
    revalidatePath("/challenges");
    return {
      ok: true,
      message: `Assigned to ${result.assigned} member(s); ${result.skipped} already had it.`,
    };
  } catch (e) {
    return fail(e);
  }
}

// ── Member ↔ challenge assignments ───────────────────────────────────────────

export async function assignChallengeToMember(
  memberId: string,
  challengeId: string,
): Promise<ActionState> {
  try {
    await apiRequest(`/members/${memberId}/challenges/${challengeId}`, {
      method: "POST",
    });
    revalidateMember(memberId);
    return { ok: true, message: "Challenge assigned." };
  } catch (e) {
    return fail(e);
  }
}

export async function addChallengeProgress(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const memberId = str(fd, "member_id");
  const challengeId = str(fd, "challenge_id");
  const amount = parseNumber(fd, "amount");
  if (!amount || amount <= 0)
    return { ok: false, error: "Enter a positive amount." };
  try {
    await apiRequest(
      `/members/${memberId}/challenges/${challengeId}/progress`,
      { method: "POST", json: { amount, description: optionalStr(fd, "description") } },
    );
    revalidateMember(memberId);
    return { ok: true, message: "Progress recorded." };
  } catch (e) {
    return fail(e);
  }
}

export async function completeChallenge(
  memberId: string,
  challengeId: string,
): Promise<ActionState> {
  try {
    await apiRequest(
      `/members/${memberId}/challenges/${challengeId}/complete`,
      { method: "POST" },
    );
    revalidateMember(memberId);
    return { ok: true, message: "Challenge completed." };
  } catch (e) {
    return fail(e);
  }
}

export async function unassignChallenge(
  memberId: string,
  challengeId: string,
): Promise<ActionState> {
  try {
    await apiRequest(`/members/${memberId}/challenges/${challengeId}`, {
      method: "DELETE",
    });
    revalidateMember(memberId);
    return { ok: true, message: "Challenge removed." };
  } catch (e) {
    return fail(e);
  }
}

// ── Tiers ────────────────────────────────────────────────────────────────────

export async function createTier(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const name = str(fd, "name");
  const minPoints = parseNumber(fd, "min_points");
  const multiplier = parseNumber(fd, "multiplier");
  if (!name) return { ok: false, error: "Name is required." };
  if (minPoints === null || minPoints < 0)
    return { ok: false, error: "Min points must be 0 or greater." };
  if (!multiplier || multiplier <= 0)
    return { ok: false, error: "Multiplier must be greater than 0." };
  try {
    await apiRequest("/tiers", {
      method: "POST",
      json: { name, min_points: minPoints, multiplier },
    });
    revalidatePath("/");
    revalidatePath("/tiers");
    return { ok: true, message: "Tier created." };
  } catch (e) {
    return fail(e);
  }
}

export async function deleteTier(id: string): Promise<ActionState> {
  try {
    await apiRequest(`/tiers/${id}`, { method: "DELETE" });
    revalidatePath("/");
    revalidatePath("/tiers");
    return { ok: true, message: "Tier deleted." };
  } catch (e) {
    return fail(e);
  }
}

// ── Segments ─────────────────────────────────────────────────────────────────

function segmentBody(fd: FormData) {
  return {
    name: str(fd, "name"),
    description: optionalStr(fd, "description"),
    color: optionalStr(fd, "color"),
  };
}

export async function createSegment(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const body = segmentBody(fd);
  if (!body.name) return { ok: false, error: "Name is required." };
  try {
    await apiRequest("/segments", { method: "POST", json: body });
    revalidatePath("/");
    revalidatePath("/segments");
    return { ok: true, message: "Segment created." };
  } catch (e) {
    return fail(e);
  }
}

export async function updateSegment(
  _prev: ActionState,
  fd: FormData,
): Promise<ActionState> {
  const id = str(fd, "id");
  const body = segmentBody(fd);
  if (!id) return { ok: false, error: "Missing segment id." };
  if (!body.name) return { ok: false, error: "Name is required." };
  try {
    await apiRequest(`/segments/${id}`, { method: "PATCH", json: body });
    revalidatePath("/");
    revalidatePath("/segments");
    return { ok: true, message: "Segment updated." };
  } catch (e) {
    return fail(e);
  }
}

export async function deleteSegment(id: string): Promise<ActionState> {
  try {
    await apiRequest(`/segments/${id}`, { method: "DELETE" });
    revalidatePath("/");
    revalidatePath("/segments");
    return { ok: true, message: "Segment deleted." };
  } catch (e) {
    return fail(e);
  }
}

export async function assignSegmentToMembers(
  segmentId: string,
  memberIds: string[],
): Promise<ActionState> {
  if (memberIds.length === 0) return { ok: false, error: "Select at least one member." };
  try {
    const result = await apiRequest<{ assigned: number; skipped: number }>(
      `/segments/${segmentId}/assign`,
      { method: "POST", json: { member_ids: memberIds } },
    );
    revalidatePath("/");
    revalidatePath("/segments");
    revalidatePath("/members");
    return {
      ok: true,
      message: `Assigned to ${result.assigned} member(s); ${result.skipped} already had it.`,
    };
  } catch (e) {
    return fail(e);
  }
}
