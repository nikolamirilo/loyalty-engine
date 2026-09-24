"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useEventTypes } from "@/lib/swr/hooks";
import { EventTypeDialog } from "@/components/events/EventTypeDialog";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { ActiveBadge } from "@/components/ui/StatusBadge";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { AlertTriangleIcon, BoltIcon, ChevronRightIcon, PlusIcon } from "@/components/ui/icons";

const MAX_ATTRIBUTE_CHIPS = 3;

export default function EventsPage() {
  const { data: eventTypes, error, mutate } = useEventTypes();
  const router = useRouter();
  const [creating, setCreating] = useState(false);

  const newEventButton = (
    <Button onClick={() => setCreating(true)}>
      <PlusIcon /> New event
    </Button>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Events"
        description="Things members do in your systems. Rules decide what each event earns."
        actions={newEventButton}
      />

      <Card className="overflow-hidden">
        {error && eventTypes === undefined ? (
          <EmptyState
            icon={<AlertTriangleIcon />}
            title="Couldn't load events"
            description={error.message}
            action={
              <Button variant="secondary" onClick={() => mutate()}>
                Retry
              </Button>
            }
          />
        ) : eventTypes === undefined ? (
          <div className="divide-y divide-line">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 px-5 py-4">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </div>
        ) : eventTypes.length === 0 ? (
          <EmptyState
            icon={<BoltIcon />}
            title="No events yet"
            description="Define an event, such as an order or an app visit, then add rules for it."
            action={newEventButton}
          />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Event</TH>
                <TH>API key</TH>
                <TH>Attributes</TH>
                <TH>Rules</TH>
                <TH>Status</TH>
                <TH />
              </TR>
            </THead>
            <TBody>
              {eventTypes.map((eventType) => {
                const href = `/admin/events/${eventType.id}`;
                const own = eventType.rules;
                const active = own.filter((r) => r.isActive).length;
                const extra = eventType.attributes.length - MAX_ATTRIBUTE_CHIPS;
                return (
                  <TR
                    key={eventType.id}
                    className="cursor-pointer hover:bg-surface-2/60"
                    onClick={() => router.push(href)}
                  >
                    <TD>
                      <Link
                        href={href}
                        onClick={(e) => e.stopPropagation()}
                        className="font-medium text-foreground hover:underline"
                      >
                        {eventType.name}
                      </Link>
                      {eventType.description && (
                        <p className="mt-0.5 max-w-xs truncate text-[0.8125rem] text-muted">
                          {eventType.description}
                        </p>
                      )}
                    </TD>
                    <TD>
                      <code className="rounded-md bg-surface-2 px-1.5 py-0.5 font-mono text-xs text-muted">
                        {eventType.key}
                      </code>
                    </TD>
                    <TD>
                      {eventType.attributes.length === 0 ? (
                        <span className="text-muted">-</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {eventType.attributes.slice(0, MAX_ATTRIBUTE_CHIPS).map((a) => (
                            <Badge key={a.key} tone="neutral">
                              {a.label}
                            </Badge>
                          ))}
                          {extra > 0 && <Badge tone="neutral">+{extra}</Badge>}
                        </div>
                      )}
                    </TD>
                    <TD className="whitespace-nowrap">
                      {own.length === 0 ? (
                        <span className="text-muted">No rules yet</span>
                      ) : (
                        <span>
                          {active} active
                          {own.length > active && (
                            <span className="text-muted"> · {own.length - active} paused</span>
                          )}
                        </span>
                      )}
                    </TD>
                    <TD>
                      <ActiveBadge active={eventType.isActive} />
                    </TD>
                    <TD className="text-right text-faint">
                      <ChevronRightIcon />
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}
      </Card>

      <EventTypeDialog open={creating} onClose={() => setCreating(false)} />
    </div>
  );
}
