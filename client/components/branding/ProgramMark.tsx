import type { Program } from "@/lib/types";
import { Avatar } from "@/components/ui/Avatar";

/**
 * The small round badge a program is shown with in lists and switchers: its
 * logo when it has one, otherwise its coloured initials. Same size as
 * `Avatar`, so the two can sit in the same list.
 *
 * The logo sits on white whatever the colour scheme, because logos are almost
 * always drawn for a light background.
 */
export function ProgramMark({ program }: { program: Pick<Program, "name" | "logoUrl"> }) {
  if (!program.logoUrl) return <Avatar name={program.name} />;
  return (
    <span
      className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-full border border-line bg-white p-1"
      aria-hidden="true"
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- see BrandLogo */}
      <img src={program.logoUrl} alt="" className="max-h-full max-w-full object-contain" />
    </span>
  );
}
