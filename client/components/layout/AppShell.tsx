"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import Image from "next/image";

import { cn } from "@/lib/format";
import { logout } from "@/lib/auth/actions";
import { preloadRoute } from "@/lib/swr/preload";
import {
  DashboardIcon,
  GiftIcon,
  LayersIcon,
  LogOutIcon,
  MenuIcon,
  TagIcon,
  TargetIcon,
  UsersIcon,
  XIcon,
} from "@/components/ui/icons";

const NAV = [
  { href: "/", label: "Dashboard", Icon: DashboardIcon, exact: true, preload: preloadRoute.dashboard },
  { href: "/members", label: "Members", Icon: UsersIcon, preload: preloadRoute.members },
  { href: "/segments", label: "Segments", Icon: TagIcon, preload: preloadRoute.segments },
  { href: "/rewards", label: "Rewards", Icon: GiftIcon, preload: preloadRoute.rewards },
  { href: "/challenges", label: "Challenges", Icon: TargetIcon, preload: preloadRoute.challenges },
  { href: "/tiers", label: "Tiers", Icon: LayersIcon, preload: preloadRoute.tiers },
];

function isActive(pathname: string, href: string, exact?: boolean): boolean {
  if (exact) return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

function Brand() {
  return (
    <Link href="/" className="flex items-center gap-2.5">
      {/* `unoptimized` skips the Image Optimizer, which rejects SVGs by
          default (returns HTTP 400) - that broken response is what flooded the
          dev console and, together with a briefly-missing `alt`, triggered the
          Fast Refresh full-reload loop. SVGs need no optimization anyway. */}
      <Image
        className="h-9 w-9 shrink-0 shadow-sm"
        src="/logo.svg"
        alt="Loyalty Engine"
        width={36}
        height={36}
        unoptimized
      />
      <span className="text-[15px] font-semibold tracking-tight text-foreground">
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
      <p className="px-3 pt-2 text-xs text-faint">Admin console · v1.0</p>
    </form>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <ul className="space-y-1">
      {NAV.map(({ href, label, Icon, exact, preload }) => {
        const active = isActive(pathname, href, exact);
        return (
          <li key={href}>
            <Link
              href={href}
              onClick={onNavigate}
              onMouseEnter={preload}
              onFocus={preload}
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

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-dvh">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-line bg-surface lg:flex">
        <div className="flex h-16 items-center border-b border-line px-5">
          <Brand />
        </div>
        <nav className="flex-1 overflow-y-auto p-3">
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
        <Brand />
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
              <Brand />
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
              <NavList onNavigate={() => setOpen(false)} />
            </nav>
            <SignOut />
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="lg:pl-64">
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
