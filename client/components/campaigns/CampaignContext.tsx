"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

import { clearCampaign, readCampaign, writeCampaign } from "@/lib/campaign-storage";
import { useMounted } from "@/lib/use-mounted";
import { useToast } from "@/components/ui/Toast";

/** Appends the signed-in member's id as `userId` on the campaign URL, adding
 * to any query string it already has. */
function withMemberId(rawUrl: string, memberId: string): string {
  const url = new URL(rawUrl);
  url.searchParams.set("userId", memberId);
  return url.toString();
}

interface CampaignContextValue {
  /** Exactly what is in the URL box, without `userId` applied. */
  draftUrl: string;
  setDraftUrl: (value: string) => void;
  /** The resolved campaign URL while one is open, else null. */
  loadedUrl: string | null;
  /** Validate the draft and open it. Reports its own errors via toast. */
  open: () => void;
  close: () => void;
  /** False until `localStorage` has been consulted on mount. */
  restored: boolean;
}

const CampaignContext = createContext<CampaignContextValue | null>(null);

/** What `localStorage` had for this member, as the state to start from.
 *
 * Called from a state initialiser, so React may run it twice in StrictMode.
 * `clearCampaign()` is idempotent, which is what makes that safe. */
function restore(memberId: string): { draftUrl: string; loadedUrl: string | null } {
  const saved = readCampaign();
  if (!saved) return { draftUrl: "", loadedUrl: null };
  if (!saved.open) return { draftUrl: saved.url, loadedUrl: null };
  try {
    return { draftUrl: saved.url, loadedUrl: withMemberId(saved.url, memberId) };
  } catch {
    // Stored link no longer parses - drop it and show the form.
    clearCampaign();
    return { draftUrl: saved.url, loadedUrl: null };
  }
}

/** Context value for the one render that happens before storage is readable. */
const UNRESTORED: CampaignContextValue = {
  draftUrl: "",
  setDraftUrl: () => {},
  loadedUrl: null,
  open: () => {},
  close: () => {},
  restored: false,
};

/**
 * Owns the campaign the member has loaded.
 *
 * This lives in MemberShell, which the `(member)` layout renders, because
 * layouts are not re-rendered on navigation - so the state here, and the
 * iframe CampaignFrame builds from it, outlive a tab switch. Holding it in the
 * Home page instead would tear the iframe down every time the member looked at
 * Wallet, and the campaign would restart from the beginning.
 */
export function CampaignProvider({
  memberId,
  children,
}: {
  memberId: string;
  children: React.ReactNode;
}) {
  // The server cannot read localStorage, so seeding state from it during
  // hydration would render a form on the server and a campaign on the client.
  // Mounting the stateful half only afterwards lets it restore in its state
  // initialisers instead of in an effect, which costs a second render pass on
  // every mount. CampaignLauncher renders nothing while `restored` is false,
  // so the inert value below is never interactive.
  const mounted = useMounted();
  if (!mounted) {
    return (
      <CampaignContext.Provider value={UNRESTORED}>{children}</CampaignContext.Provider>
    );
  }

  // Keyed by member: a different member has to re-read storage, which is what
  // the old effect's [memberId] dependency did.
  return (
    <RestoredCampaignProvider key={memberId} memberId={memberId}>
      {children}
    </RestoredCampaignProvider>
  );
}

function RestoredCampaignProvider({
  memberId,
  children,
}: {
  memberId: string;
  children: React.ReactNode;
}) {
  const [initial] = useState(() => restore(memberId));
  const [draftUrl, setDraftUrl] = useState(initial.draftUrl);
  const [loadedUrl, setLoadedUrl] = useState<string | null>(initial.loadedUrl);
  const toast = useToast();

  const open = useCallback(() => {
    const trimmed = draftUrl.trim();
    if (!trimmed) {
      toast.error("Enter a campaign URL.");
      return;
    }

    let finalUrl: string;
    try {
      finalUrl = withMemberId(trimmed, memberId);
    } catch {
      toast.error("Enter a valid campaign URL.");
      return;
    }

    setLoadedUrl(finalUrl);
    writeCampaign({ url: trimmed, open: true });
  }, [draftUrl, memberId, toast]);

  const close = useCallback(() => {
    setLoadedUrl(null);
    // Keep the link so the input comes back filled in - only the campaign is
    // dismissed, and reopening it takes one tap.
    writeCampaign({ url: draftUrl.trim(), open: false });
  }, [draftUrl]);

  const value = useMemo(
    () => ({ draftUrl, setDraftUrl, loadedUrl, open, close, restored: true }),
    [draftUrl, loadedUrl, open, close],
  );

  return (
    <CampaignContext.Provider value={value}>{children}</CampaignContext.Provider>
  );
}

export function useCampaign(): CampaignContextValue {
  const ctx = useContext(CampaignContext);
  if (!ctx) {
    throw new Error("useCampaign must be used within a CampaignProvider.");
  }
  return ctx;
}
