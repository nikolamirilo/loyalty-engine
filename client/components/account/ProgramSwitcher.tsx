"use client";

import { useState, useTransition } from "react";

import { switchMemberProgram } from "@/lib/member/programs";
import type { MemberProgram } from "@/lib/types";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useToast } from "@/components/ui/Toast";

/**
 * Lets a member move between loyalty programs.
 *
 * Each program keeps its own points, tier and history for the same person, so
 * switching changes everything the app shows. Programs they have not joined
 * are offered too: picking one signs them up, starting from zero.
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
    setError(null);
    startTransition(async () => {
      const result = await switchMemberProgram(programId);
      if (result.ok) toast.success(result.message ?? "Switched program.");
      else setError(result.error ?? "Could not switch program.");
    });
  };

  return (
    <div className="mt-5 border-t border-line pt-5">
      <label
        htmlFor="member-program"
        className="text-xs text-faint"
      >
        Loyalty program
      </label>
      <select
        id="member-program"
        value={current?.id ?? ""}
        disabled={pending}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1.5 w-full cursor-pointer rounded-lg border border-line bg-surface px-3 py-2 text-sm text-foreground disabled:opacity-60 sm:max-w-xs"
      >
        {programs.map((program) => (
          <option key={program.id} value={program.id}>
            {program.name}
            {program.memberId ? "" : " (join)"}
          </option>
        ))}
      </select>
      <p className="mt-2 text-xs text-faint">
        Your points, tier and rewards are separate in each program.
      </p>
      {error && (
        <div className="mt-3">
          <ErrorBanner message={error} />
        </div>
      )}
    </div>
  );
}
