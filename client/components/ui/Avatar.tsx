import { cn, initials } from "@/lib/format";

// Stable per-name tint so avatars are distinguishable but calm.
const PALETTE = [
  "bg-accent-blue/12 text-accent-blue",
  "bg-accent-aqua/15 text-accent-aqua",
  "bg-accent-violet/12 text-accent-violet",
  "bg-accent-orange/12 text-accent-orange",
  "bg-accent-yellow/15 text-accent-yellow",
];

function pick(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) | 0;
  return PALETTE[Math.abs(hash) % PALETTE.length];
}

export function Avatar({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
        pick(name),
        className,
      )}
      aria-hidden="true"
    >
      {initials(name)}
    </span>
  );
}
