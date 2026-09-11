"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/format";
import { CampaignProvider } from "@/components/campaigns/CampaignContext";
import { CampaignFrame } from "@/components/campaigns/CampaignFrame";
import { memberLogout } from "@/lib/memberAuth/actions";
import {
  HomeIcon,
  LogOutIcon,
  ShoppingBagIcon,
  UserIcon,
  WalletIcon,
} from "@/components/ui/icons";

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
 * inside a phone-sized frame: the same one-column layout a member sees on
 * their phone, so nothing has to be designed twice. The frame owns the
 * scrolling there, which is why the tab bar switches `fixed` -> `absolute` -
 * `fixed` would pin it to the desktop viewport instead of the frame.
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

  return (
    <CampaignProvider memberId={memberId}>
      <div className="min-h-dvh md:grid md:place-items-center md:bg-surface-2 md:p-6">
        <div className="md:relative md:h-[844px] md:max-h-[calc(100dvh-3rem)] md:w-[390px] md:overflow-hidden md:rounded-[2.25rem] md:border md:border-line md:bg-background md:shadow-2xl">
          <div className="flex min-h-dvh flex-col pb-[calc(4.5rem+env(safe-area-inset-bottom))] md:h-full md:min-h-0 md:overflow-y-auto md:pb-[4.5rem]">
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

          <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-line/70 bg-primary-subtle pb-[env(safe-area-inset-bottom)] md:absolute md:pb-0">
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
        </div>
      </div>
    </CampaignProvider>
  );
}
