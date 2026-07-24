"use client";

import { useMemo, useState } from "react";

import { assignSegmentToMembers } from "@/lib/actions";
import { useMembers } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { Segment } from "@/lib/types";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Checkbox, Input } from "@/components/ui/Field";
import { EmptyState } from "@/components/ui/EmptyState";
import { AlertTriangleIcon, UsersIcon } from "@/components/ui/icons";

export function AssignMembersDialog({ segment }: { segment: Segment }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button size="sm" variant="secondary" onClick={() => setOpen(true)}>
        <UsersIcon /> Assign members
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Assign members"
        description={`Add members to "${segment.name}".`}
        size="lg"
      >
        {/* Only mounted while open, so search/selection state resets cleanly
            on every open (matches FormDialog's FormBody pattern). */}
        <AssignMembersDialogBody segment={segment} onDone={() => setOpen(false)} />
      </Dialog>
    </>
  );
}

function AssignMembersDialogBody({
  segment,
  onDone,
}: {
  segment: Segment;
  onDone: () => void;
}) {
  const { data: members, error } = useMembers();
  const revalidate = useRevalidate();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const available = useMemo(
    () => (members ?? []).filter((m) => !m.segments.some((s) => s.id === segment.id)),
    [members, segment.id],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return available;
    return available.filter(
      (m) => m.name.toLowerCase().includes(q) || m.email.toLowerCase().includes(q),
    );
  }, [available, query]);

  const filteredIds = useMemo(() => filtered.map((m) => m.id), [filtered]);
  const allFilteredSelected =
    filteredIds.length > 0 && filteredIds.every((id) => selected.includes(id));

  const toggleAll = () => {
    setSelected((prev) => {
      if (allFilteredSelected) {
        const drop = new Set(filteredIds);
        return prev.filter((id) => !drop.has(id));
      }
      return Array.from(new Set([...prev, ...filteredIds]));
    });
  };

  const toggleOne = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  if (error && members === undefined) {
    return (
      <EmptyState
        icon={<AlertTriangleIcon />}
        title="Couldn't load members"
        description={error.message}
      />
    );
  }

  if (members !== undefined && available.length === 0) {
    return (
      <EmptyState
        icon={<UsersIcon />}
        title="Everyone's already in"
        description="Every member is already part of this segment."
      />
    );
  }

  return (
    <div className="space-y-3">
      <Input
        placeholder="Search members…"
        aria-label="Search members"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {members === undefined ? (
        <p className="py-6 text-center text-sm text-muted">Loading members…</p>
      ) : filtered.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted">
          No members match &quot;{query}&quot;.
        </p>
      ) : (
        <>
          <label className="flex cursor-pointer items-center gap-2.5 border-b border-line pb-2.5 text-sm text-foreground select-none">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-line text-primary accent-primary"
              checked={allFilteredSelected}
              onChange={toggleAll}
            />
            Select all{query ? ` (${filtered.length} matching)` : ""}
          </label>
          <ul className="max-h-[50vh] divide-y divide-line overflow-y-auto">
            {filtered.map((member) => (
              <li key={member.id} className="py-2">
                <Checkbox
                  label={`${member.name} · ${member.email}`}
                  checked={selected.includes(member.id)}
                  onChange={() => toggleOne(member.id)}
                />
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="flex items-center justify-between gap-3 border-t border-line pt-3">
        <p className="text-xs text-faint">{selected.length} selected</p>
        <ActionButton
          disabled={selected.length === 0}
          action={() => assignSegmentToMembers(segment.id, selected)}
          successMessage="Members assigned."
          onDone={() => {
            revalidate.segments();
            revalidate.members();
            onDone();
          }}
        >
          Assign{selected.length > 0 ? ` (${selected.length})` : ""}
        </ActionButton>
      </div>
    </div>
  );
}
