"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { clearCampaign, readCampaign, writeCampaign } from "@/lib/campaign-storage";
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
  const [draftUrl, setDraftUrl] = useState("");
  const [loadedUrl, setLoadedUrl] = useState<string | null>(null);
  const [restored, setRestored] = useState(false);
  const toast = useToast();

  // Restoring runs in an effect, not in the initial state: the server has no
  // access to localStorage, so seeding state from it directly would render a
  // form on the server and a campaign on the client - a hydration mismatch.
  useEffect(() => {
    const saved = readCampaign();
    if (saved) {
      setDraftUrl(saved.url);
      if (saved.open) {
        try {
          setLoadedUrl(withMemberId(saved.url, memberId));
        } catch {
          // Stored link no longer parses - drop it and show the form.
          clearCampaign();
        }
      }
    }
    setRestored(true);
  }, [memberId]);

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
    () => ({ draftUrl, setDraftUrl, loadedUrl, open, close, restored }),
    [draftUrl, loadedUrl, open, close, restored],
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
