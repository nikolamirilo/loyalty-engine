"use client";

import { useState } from "react";
import Link from "next/link";

import { formatDateTime } from "@/lib/format";
import { useEvents, useEventTypes } from "@/lib/swr/hooks";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Select } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { AlertTriangleIcon, BoltIcon, ChevronRightIcon } from "@/components/ui/icons";
import { EventEffects, eventDetails } from "./EventEffects";

/**
 * Every event received in the program, newest first: who it was for and what
 * its rules did. Filtered by event type on the server, so the list always
 * holds the latest events of the chosen type.
 */
export function EventLog() {
  const [typeKey, setTypeKey] = useState("");
  const { data: eventTypes } = useEventTypes();
  const { data: events, error, mutate } = useEvents(typeKey || undefined);
  const chosen = eventTypes?.find((t) => t.key === typeKey);

  return (
    <div className="space-y-6">
      <Link
        href="/admin/events"
        className="inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-foreground"
      >
        <ChevronRightIcon className="rotate-180 text-base" />
        All events
      </Link>

      <PageHeader
        title="Event logs"
        description="Every event received in this program, and what its rules did."
        actions={
          <div className="w-56">
            <Select
              aria-label="Filter by event"
              value={typeKey}
              onChange={(e) => setTypeKey(e.target.value)}
            >
              <option value="">All events</option>
              {(eventTypes ?? []).map((t) => (
                <option key={t.id} value={t.key}>
                  {t.name}
                </option>
              ))}
            </Select>
          </div>
        }
      />

      <Card className="overflow-hidden">
        {error && events === undefined ? (
          <EmptyState
            icon={<AlertTriangleIcon />}
            title="Couldn't load event logs"
            description={error.message}
            action={
              <Button variant="secondary" onClick={() => mutate()}>
                Retry
              </Button>
            }
          />
        ) : events === undefined ? (
          <div className="divide-y divide-line">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 px-5 py-4">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-4 w-24" />
              </div>
            ))}
          </div>
        ) : events.length === 0 ? (
          <EmptyState
            icon={<BoltIcon />}
            title={chosen ? `No "${chosen.name}" events yet` : "No events yet"}
            description="Events your systems send, and test events, will appear here."
          />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Event</TH>
                <TH>Member</TH>
                <TH>What happened</TH>
                <TH className="text-right">When</TH>
              </TR>
            </THead>
            <TBody>
              {events.map((event) => {
                const details = eventDetails(event, eventTypes);
                return (
                  <TR key={event.id} className="align-top hover:bg-surface-2/60">
                    <TD>
                      <p className="font-medium">{event.name}</p>
                      {details && <p className="mt-0.5 max-w-56 text-[0.8125rem] text-muted">{details}</p>}
                    </TD>
                    <TD>
                      <Link
                        href={`/admin/members/${event.member.id}`}
                        className="font-medium text-foreground hover:underline"
                      >
                        {event.member.name}
                      </Link>
                      <p className="mt-0.5 text-[0.8125rem] text-muted">{event.member.email}</p>
                    </TD>
                    <TD>
                      <EventEffects effects={event.effects} />
                    </TD>
                    <TD className="text-right whitespace-nowrap text-muted">{formatDateTime(event.createdAt)}</TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
