"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/format";
import { useCampaign } from "./CampaignContext";
import { RefreshIcon, XIcon } from "@/components/ui/icons";

/**
 * The campaign iframe, mounted by MemberShell rather than by the Home page.
 *
 * Because the shell is part of the `(member)` layout it is not re-rendered on
 * navigation, so this iframe - and whatever state the campaign holds inside it
 * - survives a trip to Products and back. Off Home it is hidden with
 * `display: none` rather than unmounted: removing it from the DOM (or moving it
 * to a different parent) is what forces a browser to reload an iframe, and a
 * reload is exactly what we are avoiding here.
 *
 * The reload button turns that same rule around deliberately. The campaign is
 * cross-origin, so we cannot reach into it and call `location.reload()`;
 * changing the React `key` instead throws the old iframe element away and
 * mounts a fresh one, which re-requests the URL from scratch.
 *
 * It fills MemberShell's `relative` `<main>` edge to edge, covering that
 * element's padding, so the campaign gets the whole content region. The header
 * and tab bar sit outside `<main>` and stay usable.
 */
const CONTROL_BUTTON =
  "flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-line bg-surface/90 text-lg text-muted shadow-sm backdrop-blur transition-colors hover:bg-surface hover:text-foreground";

export function CampaignFrame() {
  const { loadedUrl, close } = useCampaign();
  const pathname = usePathname();
  const [reloadNonce, setReloadNonce] = useState(0);

  if (!loadedUrl) return null;

  return (
    <div
      className={cn("absolute inset-0 bg-background", pathname !== "/home" && "hidden")}
      // The campaign keeps running while hidden, so keep it out of the
      // accessibility tree and tab order when it is not the visible page.
      aria-hidden={pathname !== "/home"}
      inert={pathname !== "/home" ? true : undefined}
    >
      <iframe
        key={`${loadedUrl}#${reloadNonce}`}
        src={loadedUrl}
        title="Campaign"
        className="h-full w-full border-0"
      />
      <div className="absolute right-3 top-3 flex items-center gap-2">
        <button
          type="button"
          onClick={() => setReloadNonce((n) => n + 1)}
          aria-label="Reload campaign"
          title="Reload campaign"
          className={CONTROL_BUTTON}
        >
          <RefreshIcon />
        </button>
        <button
          type="button"
          onClick={close}
          aria-label="Close campaign"
          title="Close campaign"
          className={CONTROL_BUTTON}
        >
          <XIcon />
        </button>
      </div>
    </div>
  );
}
