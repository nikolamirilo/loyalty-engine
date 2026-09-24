/**
 * One read-only fact on the member profile: a small label over its value, on a
 * tinted tile so a row of them reads as one set. Meant for a `<dl>` grid (see
 * `MemberProfileCard`), which gives every tile in a row the same height.
 */
export function ProfileDetail({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-w-0 rounded-lg bg-surface-2/60 px-3.5 py-3">
      <dt className="truncate text-xs text-faint" title={label}>
        {label}
      </dt>
      <dd className="mt-1 flex min-w-0 items-center gap-2 text-sm font-medium text-foreground">
        {children}
      </dd>
    </div>
  );
}

export function NotSet() {
  return <span className="font-normal text-faint">Not set</span>;
}
