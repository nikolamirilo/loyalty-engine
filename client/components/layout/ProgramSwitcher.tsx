"use client";

import { useTransition } from "react";
import Link from "next/link";

import { cn } from "@/lib/format";
import { switchProgram } from "@/lib/programs/actions";
import type { Program } from "@/lib/types";
import { Avatar } from "@/components/ui/Avatar";
import { DropdownMenu, DropdownMenuItem } from "@/components/ui/DropdownMenu";
import { Spinner } from "@/components/ui/Spinner";
import { CheckIcon, ChevronDownIcon } from "@/components/ui/icons";

/**
 * Picks which dataset the console is looking at. Everything below it in the
 * nav - members, rewards, products, challenges, tiers, segments - belongs to
 * the selected program and changes completely when this does.
 *
 * Same picker as the member app's (components/account/ProgramSwitcher): the
 * closed trigger carries the program's own colour and initials, so the console
 * always says which dataset is on screen without being read.
 */
export function ProgramSwitcher({
  programs,
  currentSlug,
}: {
  programs: Program[];
  currentSlug: string;
}) {
  const [pending, startTransition] = useTransition();

  if (programs.length === 0) return null;

  const current = programs.find((p) => p.slug === currentSlug);

  const onPick = (slug: string) => {
    // Re-picking the program already on screen would rebuild every page below
    // to land exactly where it started.
    if (pending || slug === currentSlug) return;
    const data = new FormData();
    data.set("slug", slug);
    startTransition(() => {
      void switchProgram(data);
    });
  };

  return (
    // No box: the trigger below is already a bordered control, so framing it
    // in a second border just drew a box around a box. The label and the
    // control sit directly in the nav, like the links under them.
    <div className="mb-4">
      <div className="flex items-center justify-between px-1">
        <span className="text-xs font-medium uppercase tracking-wide text-faint">
          Program
        </span>
        <Link
          href="/admin/programs"
          className="text-xs font-medium text-muted hover:text-foreground"
        >
          Manage
        </Link>
      </div>

      <DropdownMenu
        align="start"
        // Full width, and the panel matched to it, so the open menu lines up
        // with the closed control instead of hanging off one corner of it.
        className="mt-1.5 block w-full"
        panelClassName="w-full"
        trigger={
          <button
            type="button"
            disabled={pending}
            aria-haspopup="menu"
            aria-label="Selected program"
            className="flex w-full cursor-pointer items-center gap-2.5 rounded-md border border-line bg-surface px-2 py-1.5 text-left transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {current && <Avatar name={current.name} />}
            <span className="min-w-0 flex-1 truncate text-sm font-medium text-foreground">
              {current?.name ?? "Choose a program"}
            </span>
            {pending ? (
              <Spinner className="shrink-0 text-base text-muted" />
            ) : (
              <ChevronDownIcon className="shrink-0 text-base text-muted" />
            )}
          </button>
        }
      >
        {programs.map((program) => {
          const active = program.slug === currentSlug;
          return (
            <DropdownMenuItem
              key={program.id}
              onClick={() => onPick(program.slug)}
              // Marked, not disabled: a disabled item is unfocusable, so the
              // one line saying which program is current would be the one a
              // keyboard user cannot reach. `onPick` ignores it anyway.
              aria-current={active ? "true" : undefined}
              // Only a background: the item's own gap and padding are left
              // alone, since appending competing spacing utilities to a plain
              // class join leaves the winner up to stylesheet order.
              className={cn(active && "bg-primary-subtle")}
            >
              <Avatar name={program.name} />
              <span
                className={cn(
                  "min-w-0 flex-1 truncate text-sm",
                  active
                    ? "font-semibold text-primary-subtle-fg"
                    : "font-medium text-foreground",
                )}
              >
                {program.name}
              </span>
              {active && <CheckIcon className="shrink-0 text-base text-primary" />}
              <span className="sr-only">
                {active ? "Current program" : `Switch to ${program.name}`}
              </span>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenu>
    </div>
  );
}
