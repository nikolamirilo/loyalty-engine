"use client";

import { usePathname } from "next/navigation";

import { cn } from "@/lib/format";
import { useCampaign } from "./CampaignContext";
import { XIcon } from "@/components/ui/icons";

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
 * It fills MemberShell's `relative` `<main>` edge to edge, covering that
 * element's padding, so the campaign gets the whole content region. The header
 * and tab bar sit outside `<main>` and stay usable.
 */
export function CampaignFrame() {
  const { loadedUrl, close } = useCampaign();
  const pathname = usePathname();

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
        key={loadedUrl}
        src={loadedUrl}
        title="Campaign"
        className="h-full w-full border-0"
      />
      <button
        type="button"
        onClick={close}
        aria-label="Close campaign"
        className="absolute right-3 top-3 flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-line bg-surface/90 text-lg text-muted shadow-sm backdrop-blur transition-colors hover:bg-surface hover:text-foreground"
      >
        <XIcon />
      </button>
    </div>
  );
}
