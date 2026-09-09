"use client";

import { createSegment } from "@/lib/actions";
import { useSegments } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { CardGridSkeleton } from "@/components/ui/Skeletons";
import { SegmentCard } from "@/components/segments/SegmentCard";
import { SegmentFields } from "@/components/segments/SegmentFields";
import { PlusIcon, TagIcon } from "@/components/ui/icons";

function NewSegmentButton() {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <Button>
          <PlusIcon /> New segment
        </Button>
      }
      title="New segment"
      description="Segments group members so you can target them - e.g. when bulk-assigning a challenge."
      action={createSegment}
      submitLabel="Create segment"
      onSuccess={() => revalidate.segments()}
    >
      <SegmentFields />
    </FormDialog>
  );
}

export default function SegmentsPage() {
  const { data: segments } = useSegments();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Segments"
        description="Named member cohorts you can assign members to and target with challenges."
        actions={<NewSegmentButton />}
      />

      {segments === undefined ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <CardGridSkeleton count={3} />
        </div>
      ) : segments.length === 0 ? (
        <Card>
          <EmptyState
            icon={<TagIcon />}
            title="No segments yet"
            description="Create a segment (e.g. VIP or Newsletter) so you can assign members to it and target it from challenges."
            action={<NewSegmentButton />}
          />
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {segments.map((segment) => (
            <SegmentCard key={segment.id} segment={segment} />
          ))}
        </div>
      )}
    </div>
  );
}
