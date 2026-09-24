"use client";

import { useState } from "react";
import Link from "next/link";

import { sendEvent } from "@/lib/events/actions";
import { formatDateTime } from "@/lib/format";
import { useEventTypes, useMemberEvents } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { CustomAttributeValue, EventAttribute, EventType } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Field, Input, Select } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { Skeleton } from "@/components/ui/Skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import { MemberWidget } from "@/components/members/MemberWidget";
import { BoltIcon, CheckCircleIcon } from "@/components/ui/icons";

/** A member's events, newest first, each with what its rules did. */
export function MemberEventsCard({ memberId }: { memberId: string }) {
  const { data: events } = useMemberEvents(memberId);
  const { data: eventTypes } = useEventTypes();

  // Events store attribute keys; show the labels the admin defined, when the
  // event type still exists.
  const labelOf = (typeKey: string, key: string) =>
    eventTypes?.find((t) => t.key === typeKey)?.attributes.find((a) => a.key === key)?.label ?? key;

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
              <TH className="text-right">When</TH>
            </TR>
          </THead>
          <TBody>
            {events.map((event) => {
              const details = Object.entries(event.attributes)
                .map(([key, value]) => `${labelOf(event.type, key)} ${display(value)}`)
                .join(" · ");
              return (
                <TR key={event.id} className="align-top hover:bg-surface-2/60">
                  <TD>
                    <p className="font-medium">{event.name}</p>
                    {details && <p className="mt-0.5 max-w-56 text-[0.8125rem] text-muted">{details}</p>}
                  </TD>
                  <TD>
                    {event.effects.length === 0 ? (
                      <span className="text-[0.8125rem] text-muted">No rules matched</span>
                    ) : (
                      <ul className="space-y-1 text-[0.8125rem]">
                        {event.effects.map((effect, i) => (
                          <li
                            key={i}
                            title={effect.ruleName}
                            className={effect.skipped ? "text-muted" : "flex items-start gap-1.5 text-foreground"}
                          >
                            {effect.skipped ? (
                              `Skipped: ${effect.summary}`
                            ) : (
                              <>
                                <CheckCircleIcon className="mt-0.5 shrink-0 text-success-fg" />
                                {effect.summary}
                              </>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </TD>
                  <TD className="text-right whitespace-nowrap text-muted">{formatDateTime(event.createdAt)}</TD>
                </TR>
              );
            })}
          </TBody>
        </Table>
      )}
    </MemberWidget>
  );
}

function display(value: CustomAttributeValue): string {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return value === null ? "-" : String(value);
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
        {eventType?.attributes.map((attribute) => (
          <Field key={attribute.key} label={attribute.label} htmlFor={`attr-${attribute.key}`} hint="optional">
            <AttributeInput attribute={attribute} />
          </Field>
        ))}
      </div>
    </>
  );
}

function AttributeInput({ attribute }: { attribute: EventAttribute }) {
  const name = `attr.${attribute.key}`;
  const id = `attr-${attribute.key}`;
  if (attribute.type === "select" || attribute.type === "boolean") {
    const options =
      attribute.type === "boolean"
        ? [
            { value: "true", label: "Yes" },
            { value: "false", label: "No" },
          ]
        : (attribute.options ?? []).map((o) => ({ value: o, label: o }));
    return (
      <Select id={id} name={name} defaultValue="">
        <option value="">Not sent</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </Select>
    );
  }
  return (
    <Input
      id={id}
      name={name}
      type={attribute.type === "number" ? "number" : attribute.type === "date" ? "date" : "text"}
      step={attribute.type === "number" ? "any" : undefined}
    />
  );
}
