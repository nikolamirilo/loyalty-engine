import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { DashboardIcon, HomeIcon, ChevronRightIcon } from "@/components/ui/icons";

export const metadata: Metadata = {
  title: "Loyalty Engine",
};

function EntryTile({
  href,
  label,
  description,
  icon,
}: {
  href: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-4 rounded-xl border border-line bg-surface p-5 shadow-sm transition-colors hover:border-primary/40 hover:bg-surface-2/60"
    >
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary-subtle text-xl text-primary-subtle-fg">
        {icon}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block font-medium text-foreground">{label}</span>
        <span className="block truncate text-sm text-muted">{description}</span>
      </span>
      <ChevronRightIcon className="shrink-0 text-lg text-faint transition-colors group-hover:text-primary" />
    </Link>
  );
}

export default function EntryPage() {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-surface-2 px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          <Image
            src="/logo.svg"
            alt="Loyalty Engine"
            width={48}
            height={48}
            className="h-12 w-12 shadow-sm"
            priority
          />
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              Welcome to Loyalty Engine
            </h1>
            <p className="mt-0.5 text-sm text-muted">Choose how you'd like to continue</p>
          </div>
        </div>
        <div className="space-y-3">
          <EntryTile
            href="/admin/login"
            label="Continue as admin"
            description="Manage members, rewards, and tiers"
            icon={<DashboardIcon />}
          />
          <EntryTile
            href="/login"
            label="Continue as user"
            description="Track your points and rewards"
            icon={<HomeIcon />}
          />
        </div>
      </div>
    </main>
  );
}
