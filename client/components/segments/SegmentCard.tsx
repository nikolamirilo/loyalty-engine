"use client";

import { deleteSegment, updateSegment } from "@/lib/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { Segment } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { FormDialog } from "@/components/ui/FormDialog";
import { PencilIcon, TagIcon, TrashIcon } from "@/components/ui/icons";
import { SegmentFields } from "./SegmentFields";

export function SegmentCard({ segment }: { segment: Segment }) {
  const revalidate = useRevalidate();
  const onChange = () => {
    revalidate.segments();
    revalidate.members();
    revalidate.challenges();
  };
  const count = segment.member_count;

  return (
    <Card className="flex flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-surface-2 text-xl text-muted"
            style={segment.color ? { color: segment.color } : undefined}
          >
            <TagIcon />
          </span>
          <div className="min-w-0">
            <p className="truncate font-semibold text-foreground">{segment.name}</p>
            <p className="text-xs text-faint">
              {count} member{count === 1 ? "" : "s"}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <FormDialog
            trigger={
              <Button variant="ghost" size="icon" aria-label={`Edit ${segment.name}`}>
                <PencilIcon />
              </Button>
            }
            title="Edit segment"
            action={updateSegment}
            submitLabel="Save changes"
            onSuccess={onChange}
          >
            <input type="hidden" name="id" value={segment.id} />
            <SegmentFields segment={segment} />
          </FormDialog>
          <ConfirmButton
            trigger={
              <Button
                variant="ghost"
                size="icon"
                aria-label={`Delete ${segment.name}`}
                className="text-danger"
              >
                <TrashIcon />
              </Button>
            }
            title={`Delete "${segment.name}"?`}
            description="Members lose this segment, and it's removed from any challenge it was bulk-assigned to. This cannot be undone."
            confirmLabel="Delete segment"
            action={deleteSegment.bind(null, segment.id)}
            successMessage="Segment deleted."
            onSuccess={onChange}
          />
        </div>
      </div>
      {segment.description && (
        <p className="mt-3 line-clamp-2 text-[13px] text-muted">{segment.description}</p>
      )}
    </Card>
  );
}
