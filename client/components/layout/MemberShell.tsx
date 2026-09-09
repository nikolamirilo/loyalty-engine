"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/format";
import { memberLogout } from "@/lib/memberAuth/actions";
import { HomeIcon, LogOutIcon, PackageIcon, WalletIcon } from "@/components/ui/icons";

const TABS = [
  { href: "/home", label: "Home", Icon: HomeIcon },
  { href: "/products", label: "Products", Icon: PackageIcon },
  { href: "/wallet", label: "Wallet", Icon: WalletIcon },
];

/**
 * The member-facing app shell: a slim top bar and a fixed bottom tab bar,
 * always visible (not just on mobile) - this is the "as-app" experience the
 * member side asked for, distinct from the admin `AppShell`'s responsive
 * sidebar/drawer.
 */
export function MemberShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-dvh pb-20">
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b border-line bg-surface/85 px-4 backdrop-blur">
        <div className="flex items-center gap-2.5">
          <Image
            className="h-8 w-8 shrink-0 shadow-sm"
            src="/logo.svg"
            alt="Loyalty Engine"
            width={32}
            height={32}
            unoptimized
          />
          <span className="text-[15px] font-semibold tracking-tight text-foreground">
            Loyalty Engine
          </span>
        </div>
        <form action={memberLogout}>
          <button
            type="submit"
            aria-label="Sign out"
            className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-lg text-muted hover:bg-surface-2 hover:text-foreground"
          >
            <LogOutIcon />
          </button>
        </form>
      </header>

      <main className="mx-auto max-w-lg px-4 py-6">{children}</main>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface/95 backdrop-blur pb-[env(safe-area-inset-bottom)]">
        <div className="mx-auto flex max-w-lg items-stretch justify-around">
          {TABS.map(({ href, label, Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex flex-1 flex-col items-center gap-1 py-2.5 text-xs font-medium transition-colors",
                  active ? "text-primary" : "text-muted hover:text-foreground",
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-12 items-center justify-center rounded-lg text-xl",
                    active && "bg-primary-subtle text-primary-subtle-fg",
                  )}
                >
                  <Icon />
                </span>
                {label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
