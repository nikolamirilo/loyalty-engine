"use client";

import { useRef } from "react";
import Link from "next/link";

import { switchProgram } from "@/lib/programs/actions";
import type { Program } from "@/lib/types";

/**
 * Picks which dataset the console is looking at. Everything below it in the
 * nav - members, rewards, products, challenges, tiers, segments - belongs to
 * the selected program and changes completely when this does.
 */
export function ProgramSwitcher({
  programs,
  currentSlug,
}: {
  programs: Program[];
  currentSlug: string;
}) {
  const form = useRef<HTMLFormElement>(null);

  if (programs.length === 0) return null;

  return (
    <div className="mb-3 rounded-lg border border-line bg-surface-2 p-3">
      <div className="flex items-center justify-between">
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
      <form ref={form} action={switchProgram}>
        <select
          name="slug"
          defaultValue={currentSlug}
          aria-label="Selected program"
          // Submitting on change keeps this to one control: there is no reason
          // to make someone pick a program and then press a second button.
          onChange={() => form.current?.requestSubmit()}
          className="mt-1.5 w-full cursor-pointer rounded-md border border-line bg-surface px-2 py-1.5 text-sm font-medium text-foreground"
        >
          {programs.map((program) => (
            <option key={program.id} value={program.slug}>
              {program.name}
            </option>
          ))}
        </select>
      </form>
    </div>
  );
}
