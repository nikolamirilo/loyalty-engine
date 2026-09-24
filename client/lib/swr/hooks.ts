"use client";

import useSWR from "swr";

import type {
  Challenge,
  ChallengeAssignment,
  EventType,
  Member,
  MemberAttribute,
  MemberEvent,
  MemberStats,
  PointsTransaction,
  Product,
  Purchase,
  PurchaseStats,
  Redemption,
  Reward,
  Segment,
  Tier,
} from "@/lib/types";
import { keys } from "./keys";

/**
 * Typed read hooks - the single entry point for component data access. The
 * global fetcher is configured once in app/admin/(protected)/providers.tsx
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

export function useProducts(activeOnly = false) {
  return useSWR<Product[]>(keys.products(activeOnly));
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

export function useMemberPurchases(id: string | undefined) {
  return useSWR<Purchase[]>(id ? keys.memberPurchases(id) : null);
}

export function usePurchaseStats(id: string | undefined, days?: number) {
  return useSWR<PurchaseStats>(id ? keys.purchaseStats(id, days) : null);
}

export function useMemberChallenges(id: string | undefined) {
  return useSWR<ChallengeAssignment[]>(id ? keys.memberChallenges(id) : null);
}

export function useSegments() {
  return useSWR<Segment[]>(keys.segments());
}

export function useMemberAttributes() {
  return useSWR<MemberAttribute[]>(keys.memberAttributes());
}

export function useEventTypes() {
  return useSWR<EventType[]>(keys.eventTypes());
}

export function useEventType(id: string | undefined) {
  return useSWR<EventType>(id ? keys.eventType(id) : null);
}

export function useMemberEvents(id: string | undefined) {
  return useSWR<MemberEvent[]>(id ? keys.memberEvents(id) : null);
}
