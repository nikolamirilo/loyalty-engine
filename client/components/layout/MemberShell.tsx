"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { cn } from "@/lib/format";
import { CampaignProvider } from "@/components/campaigns/CampaignContext";
import { CampaignFrame } from "@/components/campaigns/CampaignFrame";
import { memberLogout } from "@/lib/memberAuth/actions";
import {
  BatteryIcon,
  HomeIcon,
  LogOutIcon,
  ShoppingBagIcon,
  SignalIcon,
  UserIcon,
  WalletIcon,
  WifiIcon,
} from "@/components/ui/icons";

// The desktop frame's design height (paired with the 390px design width set
// on the frame div below) - the same "phone" dimensions the mobile layout
// renders at. Everything inside is authored against these dimensions, then
// the whole frame is scaled up via `transform: scale()` (see the `scale`
// state below) so the header, tab bar, icons, and text all grow together
// instead of only the container stretching around fixed-size children.
const FRAME_HEIGHT = 844;

const TABS = [
  { href: "/home", label: "Home", Icon: HomeIcon },
  // Same icon as the admin console's Products nav item (AppShell.tsx).
  { href: "/products", label: "Products", Icon: ShoppingBagIcon },
  { href: "/wallet", label: "Wallet", Icon: WalletIcon },
  { href: "/account", label: "Account", Icon: UserIcon },
];

/**
 * The member-facing app shell: a slim top bar and a fixed bottom tab bar,
 * always visible (not just on mobile) - this is the "as-app" experience the
 * member side asked for, distinct from the admin `AppShell`'s responsive
 * sidebar/drawer.
 *
 * On a phone it fills the screen and scrolls the document, so the browser
 * chrome collapses the way a native app's would. From `md` up it is centered
 * inside a phone-sized frame styled as an actual device (titanium bezel, side
 * buttons, punch-hole camera, Android status bar, gesture-nav pill) - the
 * same one-column layout a member sees on their phone, so nothing has to be
 * designed twice, now dressed up as an emulator instead of a bare rectangle.
 * All of that chrome is `hidden md:*` - a real phone already supplies its own
 * status bar and gesture bar, so none of it should render there.
 *
 * The device face owns the scrolling at `md`, which is why the tab bar
 * switches `fixed` -> `absolute` - `fixed` would pin it to the desktop
 * viewport instead of the frame. The status bar and gesture pill sit outside
 * the scrolling wrapper (as siblings, not children) so they stay put while
 * the app content scrolls beneath them, the way real device chrome does.
 *
 * `<main>` is a `relative` flex child that grows into the space left between
 * the header and the tab bar, so a page can fill the content region exactly
 * (`absolute inset-0`) without knowing either of their heights. CampaignFrame
 * relies on this, and is mounted here rather than in the Home page so the
 * campaign iframe is not torn down and reloaded on every tab switch.
 */
export function MemberShell({
  memberId,
  children,
}: {
  memberId: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  // `null` means "not desktop" (or not yet measured) - the frame then renders
  // at its natural CSS size with no transform, so `position: fixed` in the
  // mobile tab bar keeps working (any transform, even `scale(1)`, turns an
  // ancestor into a containing block for fixed descendants).
  const [scale, setScale] = useState<number | null>(null);

  useEffect(() => {
    const mql = window.matchMedia("(min-width: 768px)");
    const updateScale = () => {
      setScale(mql.matches ? (window.innerHeight * 0.9) / FRAME_HEIGHT : null);
    };
    updateScale();
    window.addEventListener("resize", updateScale);
    mql.addEventListener("change", updateScale);
    return () => {
      window.removeEventListener("resize", updateScale);
      mql.removeEventListener("change", updateScale);
    };
  }, []);

  return (
    <CampaignProvider memberId={memberId}>
      <div className="min-h-dvh md:grid md:h-dvh md:place-items-center md:overflow-hidden md:bg-surface-2 md:p-6">
        {/* The phone body: a 390x844 black slab that the scale transform
            sizes to 90dvh. It deliberately does not clip its overflow, so the
            side buttons can protrude past its edge. Centering it against a
            container pinned to exactly the viewport height (`md:h-dvh`, not
            `min-h-dvh`) is what keeps top/bottom space even - a `min-h`
            container would grow to fit the body's unscaled 844px layout box
            on shorter screens and push the page into a top-scrolled,
            off-center state. */}
        <div
          className="md:relative md:h-[844px] md:w-[390px] md:rounded-[3rem] md:bg-neutral-800 md:shadow-xl"
          style={scale ? { transform: `scale(${scale})` } : undefined}
        >
          {/* Side buttons - purely decorative, desktop-only. They protrude a
              couple of px past the body, which is why the body must not clip
              its overflow. */}
          <div className="pointer-events-none absolute -right-[2px] top-[92px] hidden h-16 w-[3px] rounded-r-sm bg-neutral-700 md:block" />
          <div className="pointer-events-none absolute -right-[2px] top-[168px] hidden h-11 w-[3px] rounded-r-sm bg-neutral-700 md:block" />

          {/* Device face: the display, inset inside the black body so the body
              reads as an even bezel on all four sides. `md:min-h-0` is
              load-bearing - the unprefixed `min-h-dvh` the mobile layout needs
              would otherwise win over the height implied by `inset`, blowing
              the face out to a full viewport tall and past the body. */}
          <div className="relative flex min-h-dvh flex-col md:absolute md:inset-[10px] md:min-h-0 md:overflow-hidden md:rounded-[2.4rem] md:bg-background">
            {/* Punch-hole camera, vertically centered in the status bar. */}
            <div className="pointer-events-none absolute left-1/2 top-[9px] z-50 hidden h-2.5 w-2.5 -translate-x-1/2 rounded-full bg-black md:block" />

            {/* Android status bar - sits outside the scrolling wrapper so it
                stays put while app content scrolls beneath it. */}
            <div className="hidden h-7 shrink-0 items-center justify-between px-5 text-[11px] font-semibold text-foreground md:flex">
              <span>9:41</span>
              <div className="flex items-center gap-1.5">
                <SignalIcon className="text-xs" />
                <WifiIcon className="text-xs" />
                <BatteryIcon className="text-sm" />
              </div>
            </div>

            <div className="flex flex-1 flex-col pb-[calc(4.5rem+env(safe-area-inset-bottom))] md:min-h-0 md:overflow-y-auto md:pb-[82px]">
              <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b border-line/70 bg-surface px-4 pt-[env(safe-area-inset-top)]">
                {/* Both side slots are `flex-1`, so the title sits on the true
                    center of the bar even though the logo and the button are not
                    the same width. */}
                <div className="flex flex-1 items-center">
                  <Image
                    className="h-8 w-8 shrink-0"
                    src="/logo.svg"
                    alt="Loyalty App"
                    width={32}
                    height={32}
                    unoptimized
                  />
                </div>
                <span className="truncate text-lg font-semibold tracking-tight text-primary">
                  Loyalty App
                </span>
                <div className="flex flex-1 justify-end">
                  <form action={memberLogout}>
                    <button
                      type="submit"
                      aria-label="Sign out"
                      title="Sign out"
                      className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-full text-lg text-primary transition-colors hover:bg-primary/10"
                    >
                      <LogOutIcon />
                    </button>
                  </form>
                </div>
              </header>

              <main className="relative mx-auto w-full max-w-lg flex-1 px-4 py-6">
                {children}
                <CampaignFrame />
              </main>
            </div>

            <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-line/70 bg-primary-subtle pb-[env(safe-area-inset-bottom)] md:absolute md:pb-2.5">
              <div className="mx-auto flex h-[4.5rem] max-w-lg items-stretch justify-around">
                {TABS.map(({ href, label, Icon }) => {
                  const active = pathname === href;
                  return (
                    <Link
                      key={href}
                      href={href}
                      // The member app is exactly four tabs, all of them on screen
                      // at all times, so preloading the lot is cheap and covers
                      // every navigation the member can make. `prefetch` defaults
                      // to prefetching a dynamic route only down to its loading
                      // boundary; these pages read the session cookie and are all
                      // dynamic, so the default would still leave the data fetch
                      // for click time. `true` pulls the rendered page and its
                      // data ahead of the tap. (Production only - Next disables
                      // prefetching in dev.)
                      prefetch
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "relative flex flex-1 flex-col items-center justify-center gap-1.5 px-2 text-xs transition-colors",
                        active
                          ? "font-semibold text-primary"
                          : "font-medium text-muted hover:text-foreground",
                      )}
                    >
                      {/* The selection marker is a rule across the top of the tab
                          rather than a pill behind the icon, so the icon and label
                          stay on the same baseline in every tab. */}
                      {active && (
                        <span
                          aria-hidden
                          className="absolute inset-x-3 top-0 h-[3px] rounded-full bg-primary"
                        />
                      )}
                      {/* The icon set is stroked outlines; the active tab washes
                          its interior with the same color so it reads as filled
                          next to the outline-only tabs, as the design asks. */}
                      <Icon
                        className="text-2xl"
                        fill={active ? "currentColor" : "none"}
                        fillOpacity={active ? 0.2 : undefined}
                      />
                      {label}
                    </Link>
                  );
                })}
              </div>
            </nav>

            {/* Android gesture-nav pill, in the 10px band the tab bar's
                `md:pb-2.5` reserves for it. */}
            <div className="pointer-events-none absolute bottom-[3px] left-1/2 z-50 hidden h-1 w-28 -translate-x-1/2 rounded-full bg-foreground/50 md:block" />
          </div>
        </div>
      </div>
    </CampaignProvider>
  );
}
