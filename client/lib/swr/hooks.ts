"use client";

import useSWR from "swr";

import type {
  Challenge,
  ChallengeAssignment,
  Member,
  MemberStats,
  PointsTransaction,
  Redemption,
  Reward,
  Segment,
  Tier,
} from "@/lib/types";
import { keys } from "./keys";

/**
 * Typed read hooks - the single entry point for component data access. The
 * global fetcher is configured once in app/(protected)/providers.tsx
 * (SWRConfig), so hooks only supply the key. Passing `undefined`/empty id
 * yields a `null` key, which tells SWR not to fetch yet.
 */

export function useMembers(
  opts: { skip?: number; limit?: number; q?: string } = {},
) {
  return useSWR<Member[]>(keys.members(opts));
}

export function useMembersCount(q?: string) {
  return useSWR<{ count: number }>(keys.membersCount(q));
}

export function useMemberStats() {
  return useSWR<MemberStats>(keys.memberStats());
}

export function useMember(id: string | undefined) {
  return useSWR<Member>(id ? keys.member(id) : null);
}

export function useTiers() {
  return useSWR<Tier[]>(keys.tiers());
}

export function useRewards(activeOnly = false) {
  return useSWR<Reward[]>(keys.rewards(activeOnly));
}

export function useChallenges(activeOnly = false) {
  return useSWR<Challenge[]>(keys.challenges(activeOnly));
}

export function useTransactions(id: string | undefined) {
  return useSWR<PointsTransaction[]>(id ? keys.transactions(id) : null);
}

export function useRedemptions(id: string | undefined) {
  return useSWR<Redemption[]>(id ? keys.redemptions(id) : null);
}

export function useMemberChallenges(id: string | undefined) {
  return useSWR<ChallengeAssignment[]>(id ? keys.memberChallenges(id) : null);
}

export function useSegments() {
  return useSWR<Segment[]>(keys.segments());
}
