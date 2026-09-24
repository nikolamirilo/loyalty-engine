"use client";

import { useState } from "react";
import Link from "next/link";

import { sendEvent } from "@/lib/events/actions";
import { formatDateTime } from "@/lib/format";
import { useEventTypes, useMemberEvents } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { EventType, MemberEvent } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { Field, Select } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { Skeleton } from "@/components/ui/Skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { MemberWidget } from "@/components/members/MemberWidget";
import { EventAttributeFields } from "@/components/events/EventAttributeFields";
import { EventEffects } from "@/components/events/EventEffects";
import { BoltIcon, ChevronRightIcon } from "@/components/ui/icons";

/** A member's events, newest first, each with what its rules did. Clicking one
 * shows the whole event as JSON. */
export function MemberEventsCard({ memberId }: { memberId: string }) {
  const { data: events } = useMemberEvents(memberId);
  const { data: eventTypes } = useEventTypes();
  const [selected, setSelected] = useState<MemberEvent | null>(null);

  return (
    <MemberWidget
      title="Events"
      description="What this member did, and what the rules gave them"
      action={<SendEventButton memberId={memberId} eventTypes={eventTypes ?? []} />}
    >
      {events === undefined ? (
        <div className="divide-y divide-line">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-3.5">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-24" />
            </div>
          ))}
        </div>
      ) : events.length === 0 ? (
        <EmptyState
          icon={<BoltIcon />}
          title="No events yet"
          description="Events your systems send for this member will appear here."
        />
      ) : (
        <Table>
          <THead>
            <TR>
              <TH>Event</TH>
              <TH>What happened</TH>
              <TH>When</TH>
              <TH className="w-8" />
            </TR>
          </THead>
          <TBody>
            {events.map((event) => (
              <TR
                key={event.id}
                className="group cursor-pointer align-top hover:bg-surface-2/60"
                onClick={() => setSelected(event)}
              >
                <TD>
                  {/* No handler of its own: the click bubbles to the row. The
                      button is what makes the row reachable by keyboard. */}
                  <button type="button" className="cursor-pointer text-left font-medium hover:underline">
                    {event.name}
                  </button>
                </TD>
                <TD>
                  <EventEffects effects={event.effects} />
                </TD>
                <TD className="whitespace-nowrap text-muted">{formatDateTime(event.createdAt)}</TD>
                <TD className="text-faint transition-colors group-hover:text-foreground">
                  <ChevronRightIcon className="text-base" />
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}
      {selected && (
        <Dialog
          open
          onClose={() => setSelected(null)}
          title={selected.name}
          description={formatDateTime(selected.createdAt)}
          size="lg"
        >
          <pre className="max-h-[60vh] overflow-auto rounded-lg bg-surface-2 p-4 font-mono text-xs leading-relaxed text-foreground">
            {JSON.stringify(selected, null, 2)}
          </pre>
        </Dialog>
      )}
    </MemberWidget>
  );
}

function SendEventButton({ memberId, eventTypes }: { memberId: string; eventTypes: EventType[] }) {
  const revalidate = useRevalidate();
  return (
    <FormDialog
      trigger={
        <Button size="sm" variant="secondary">
          <BoltIcon /> Send event
        </Button>
      }
      title="Send an event"
      description="Record an event for this member, the way your systems would. Its rules run right away."
      action={sendEvent}
      submitLabel="Send event"
      onSuccess={() => {
        // Rules can move points, prizes, challenges and segments.
        revalidate.members();
        revalidate.segments();
        revalidate.events();
      }}
    >
      <input type="hidden" name="memberId" value={memberId} />
      <SendEventFields eventTypes={eventTypes.filter((t) => t.isActive)} />
    </FormDialog>
  );
}

function SendEventFields({ eventTypes }: { eventTypes: EventType[] }) {
  const [chosen, setChosen] = useState("");
  // Falls back to the first event, so the dialog works even when it opened
  // before the event list finished loading.
  const typeKey = chosen || eventTypes[0]?.key || "";
  const eventType = eventTypes.find((t) => t.key === typeKey);

  if (!eventTypes.length) {
    return (
      <p className="text-sm text-muted">
        There are no active events yet.{" "}
        <Link href="/admin/events" className="font-medium text-foreground underline">
          Define one
        </Link>{" "}
        first.
      </p>
    );
  }

  return (
    <>
      <Field label="Event" htmlFor="send-event-type">
        <Select id="send-event-type" name="type" value={typeKey} onChange={(e) => setChosen(e.target.value)}>
          {eventTypes.map((t) => (
            <option key={t.id} value={t.key}>
              {t.name}
            </option>
          ))}
        </Select>
      </Field>
      {/* Keyed by event type so switching types clears the inputs. */}
      <div key={typeKey} className="space-y-4">
        <EventAttributeFields attributes={eventType?.attributes ?? []} />
      </div>
    </>
  );
}
