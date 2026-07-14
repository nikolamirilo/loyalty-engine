import type { Member, Tier } from "./types";

/** Join truthy class names. A tiny stand-in for `clsx`. */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

/** 1284 -> "1,284" */
export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

/** Compact form for stat tiles: 1,284 / 12.9K / 4.2M */
export function compactNumber(n: number): string {
  if (Math.abs(n) < 10_000) return formatNumber(n);
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n);
}

/** Signed points, e.g. "+100" / "-30". */
export function signedNumber(n: number): string {
  return `${n > 0 ? "+" : ""}${formatNumber(n)}`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = parseUtc(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = parseUtc(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/**
 * The API stores naive UTC timestamps and serializes them without a timezone
 * suffix. Treat a suffix-less ISO string as UTC so local rendering is correct.
 */
function parseUtc(iso: string): Date {
  const hasZone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso);
  return new Date(hasZone ? iso : `${iso}Z`);
}

/** ISO timestamp -> value for an <input type="datetime-local"> in local time. */
export function toDatetimeLocalValue(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = parseUtc(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours(),
  )}:${pad(d.getMinutes())}`;
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** "in_progress" -> "In progress" */
export function humanize(value: string): string {
  const s = value.replace(/[_-]+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Compute a member's current tier from their balance, mirroring the server's
 * rule: the highest tier whose `min_points` the balance meets or exceeds.
 * Assumes `tiers` is sorted ascending by `min_points`.
 */
export function tierForBalance(tiers: Tier[], balance: number): Tier | null {
  let current: Tier | null = null;
  for (const tier of tiers) {
    if (balance >= tier.min_points) current = tier;
  }
  return current;
}

export function memberTier(tiers: Tier[], member: Member): Tier | null {
  return tierForBalance(tiers, member.pointsBalance);
}
