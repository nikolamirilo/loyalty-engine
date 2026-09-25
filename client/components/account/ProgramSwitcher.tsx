"use client";

import { useState, useTransition } from "react";

import { cn } from "@/lib/format";
import { switchMemberProgram } from "@/lib/member/programs";
import type { MemberProgram } from "@/lib/types";
import { ProgramMark } from "@/components/branding/ProgramMark";
import { Card } from "@/components/ui/Card";
import { DropdownMenu, DropdownMenuItem } from "@/components/ui/DropdownMenu";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import { useToast } from "@/components/ui/Toast";
import { CheckIcon, ChevronDownIcon } from "@/components/ui/icons";

/**
 * Lets a member move between loyalty programs.
 *
 * Members are global: the same person belongs to every program and holds a
 * separate points balance, tier and history in each. So every program is
 * offered, and switching changes everything the app shows - a program they
 * have never used simply shows zero rather than being absent.
 *
 * The closed trigger doubles as the answer to "which program am I in", which
 * is why it carries the program's logo (or its colour and initials) rather
 * than just its name - two brands then differ at a glance instead of by reading.
 *
 * Owns its own card so the whole block disappears together when there is
 * nowhere to switch to.
 */
export function ProgramSwitcher({
  programs,
  currentMemberId,
}: {
  programs: MemberProgram[];
  currentMemberId: string;
}) {
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const toast = useToast();

  if (programs.length <= 1) return null;

  const current = programs.find((p) => p.memberId === currentMemberId);

  const onChange = (programId: string) => {
    // Re-picking the program already showing would tear the session down and
    // rebuild it to land exactly where it started.
    if (pending || programId === current?.id) return;
    setError(null);
    startTransition(async () => {
      const result = await switchMemberProgram(programId);
      if (result.ok) toast.success(result.message ?? "Switched program.");
      else setError(result.error ?? "Could not switch program.");
    });
  };

  return (
    <Card className="p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-faint">
        Switch Loyalty Program
      </p>

      <DropdownMenu
        align="start"
        // Full width, and the panel matched to it, so the open menu lines up
        // with the closed control instead of hanging off one corner of it.
        className="mt-2 block w-full"
        panelClassName="w-full"
        trigger={
          <button
            type="button"
            disabled={pending}
            aria-haspopup="menu"
            className="flex w-full cursor-pointer items-center gap-3 rounded-lg border border-line bg-surface px-3 py-2.5 text-left transition-colors hover:bg-surface-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {current && <ProgramMark program={current} />}
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
          const active = program.id === current?.id;
          return (
            <DropdownMenuItem
              key={program.id}
              onClick={() => onChange(program.id)}
              // Marked, not disabled: a disabled item is unfocusable, so the
              // one line a screen-reader user most needs - which program is
              // current - would be the one they cannot reach. `onChange`
              // ignores it anyway.
              aria-current={active ? "true" : undefined}
              // Only a background: the item's own gap and padding are left
              // alone, since appending competing spacing utilities to a plain
              // class join leaves the winner up to stylesheet order.
              className={cn(active && "bg-primary-subtle")}
            >
              <ProgramMark program={program} />
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

      {error && (
        <div className="mt-3">
          <ErrorBanner message={error} />
        </div>
      )}
    </Card>
  );
}
