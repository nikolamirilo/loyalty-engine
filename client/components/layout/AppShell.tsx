"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/format";
import { BrandLogo } from "@/components/branding/BrandLogo";
import { logout } from "@/lib/auth/actions";
import type { Program } from "@/lib/types";
import { usePreload, type PreloadRoute } from "@/lib/swr/preload";
import {
  BoltIcon,
  DashboardIcon,
  GiftIcon,
  LayersIcon,
  LogOutIcon,
  MenuIcon,
  ShoppingBagIcon,
  TagIcon,
  TargetIcon,
  UsersIcon,
  XIcon,
} from "@/components/ui/icons";

// Warming is named rather than bound here: the warmer now writes into the
// cache the surrounding SWRConfig provides, so it can only be resolved from
// inside a component.
const NAV: {
  href: string;
  label: string;
  Icon: typeof DashboardIcon;
  exact?: boolean;
  preload: PreloadRoute;
}[] = [
  { href: "/admin/dashboard", label: "Dashboard", Icon: DashboardIcon, exact: true, preload: "dashboard" },
  { href: "/admin/members", label: "Members", Icon: UsersIcon, preload: "members" },
  { href: "/admin/segments", label: "Segments", Icon: TagIcon, preload: "segments" },
  { href: "/admin/rewards", label: "Rewards", Icon: GiftIcon, preload: "rewards" },
  { href: "/admin/products", label: "Products", Icon: ShoppingBagIcon, preload: "products" },
  { href: "/admin/challenges", label: "Challenges", Icon: TargetIcon, preload: "challenges" },
  { href: "/admin/events", label: "Events", Icon: BoltIcon, preload: "events" },
  { href: "/admin/tiers", label: "Tiers", Icon: LayersIcon, preload: "tiers" },
];

function isActive(pathname: string, href: string, exact?: boolean): boolean {
  if (exact) return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

type ShellProgram = Pick<Program, "name" | "logoUrl"> | null;

/** The selected program's logo when it has one, beside the product name - a
 * branded demo reads as "Lidl's loyalty engine" rather than ours. */
function Brand({ program }: { program: ShellProgram }) {
  const logoUrl = program?.logoUrl;
  return (
    <Link href="/admin/dashboard" className="flex min-w-0 items-center gap-2.5">
      <BrandLogo
        src={logoUrl}
        alt={logoUrl && program ? program.name : "Loyalty Engine"}
        className={cn("h-9 max-w-28", !logoUrl && "shadow-sm")}
      />
      <span className="text-[0.9375rem] font-semibold tracking-tight text-foreground">
        Loyalty Engine
      </span>
    </Link>
  );
}

function SignOut() {
  return (
    <form action={logout} className="border-t border-line p-3">
      <button
        type="submit"
        className="flex w-full cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted transition-colors hover:bg-surface-2 hover:text-foreground"
      >
        <LogOutIcon className="text-lg" />
        Sign out
      </button>
    </form>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const preloader = usePreload();
  return (
    <ul className="space-y-1">
      {NAV.map(({ href, label, Icon, exact, preload }) => {
        const warm = preloader.route[preload];
        const active = isActive(pathname, href, exact);
        return (
          <li key={href}>
            <Link
              href={href}
              onClick={onNavigate}
              onMouseEnter={warm}
              onFocus={warm}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary-subtle text-primary-subtle-fg"
                  : "text-muted hover:bg-surface-2 hover:text-foreground",
              )}
            >
              <Icon className="text-lg" />
              {label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

export function AppShell({
  program = null,
  programSwitcher,
  children,
}: {
  /** The selected program, for its logo; without one the stock logo shows. */
  program?: ShellProgram;
  /** Rendered above the nav. Built on the server, so it arrives as a node. */
  programSwitcher?: React.ReactNode;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-dvh">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 flex-col border-r border-line bg-surface lg:flex">
        <div className="flex h-16 items-center border-b border-line px-5">
          <Brand program={program} />
        </div>
        <nav className="flex-1 overflow-y-auto p-3">
          {programSwitcher}
          <NavList />
        </nav>
        <SignOut />
      </aside>

      {/* Mobile header */}
      <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-surface/85 px-4 backdrop-blur lg:hidden">
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open navigation"
          className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-xl text-muted hover:bg-surface-2 hover:text-foreground"
        >
          <MenuIcon />
        </button>
        <Brand program={program} />
      </header>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 animate-fade-in bg-black/40"
            onClick={() => setOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85%] flex-col border-r border-line bg-surface shadow-xl">
            <div className="flex h-14 items-center justify-between border-b border-line px-4">
              <Brand program={program} />
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
                className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-xl text-muted hover:bg-surface-2 hover:text-foreground"
              >
                <XIcon />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto p-3">
              {programSwitcher}
              <NavList onNavigate={() => setOpen(false)} />
            </nav>
            <SignOut />
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="lg:pl-72">
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
