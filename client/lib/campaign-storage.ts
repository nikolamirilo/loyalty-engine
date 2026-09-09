/**
 * Persistence for the member's campaign link (see CampaignLauncher).
 *
 * Kept apart from the component so the storage medium is a single, swappable
 * decision rather than something smeared through the UI.
 *
 * `localStorage` rather than a cookie, deliberately: Home is prefetched with
 * `prefetch` on the tab bar and cached client-side for `staleTimes.static`, so
 * a cookie read during the server render could be baked into a payload from
 * before the campaign was opened - navigating back to Home would show a stale
 * form. Reading on mount sidesteps the router cache entirely. It also keeps a
 * pure-UI preference off every request to the server.
 *
 * Only the raw URL the member typed is stored; the `userId` parameter is
 * re-applied on load from the current session, so a stored link can never
 * carry a previous member's id.
 */

const KEY = "loyaltyEngine.campaign";

export interface StoredCampaign {
  /** Exactly what the member typed, without `userId` applied. */
  url: string;
  /** Whether the campaign was on screen when they last left Home. */
  open: boolean;
}

/**
 * Every access is guarded: `localStorage` throws on access in Safari's private
 * mode and when a browser blocks third-party storage, and this is a
 * convenience, never something worth breaking Home over.
 */
export function readCampaign(): StoredCampaign | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    const { url, open } = parsed as Partial<StoredCampaign>;
    if (typeof url !== "string" || !url) return null;
    return { url, open: open === true };
  } catch {
    return null;
  }
}

export function writeCampaign(value: StoredCampaign): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    // Storage unavailable or full - the campaign still works for this visit.
  }
}

export function clearCampaign(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    // Nothing to do - see writeCampaign.
  }
}
