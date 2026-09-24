"use client";

import { useActionState, useEffect, useState } from "react";

import { idleState } from "@/lib/action-state";
import { sendEvent } from "@/lib/events/actions";
import { useMembers } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { EventType, Member } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Field, Select } from "@/components/ui/Field";
import { SubmitButton } from "@/components/ui/SubmitButton";
import { useToast } from "@/components/ui/Toast";
import { BoltIcon } from "@/components/ui/icons";
import { EventAttributeFields } from "./EventAttributeFields";

function memberOptionLabel(member: Member): string {
  return `${member.name} · ${member.email}`;
}

/**
 * Test one specific event, from its own page. The event stays fixed to the
 * program it's already shown in (an event only exists in one program), so
 * this only needs a member - picked from that same program's members.
 */
export function TestEventButton({ eventType }: { eventType: EventType }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        variant="secondary"
        onClick={() => setOpen(true)}
        disabled={!eventType.isActive}
        title={eventType.isActive ? undefined : "Turn this event on to test it."}
      >
        <BoltIcon /> Test event
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={`Test "${eventType.name}"`}
        description="Send this event for a member you choose. Its rules run right away."
      >
        {/* Only mounted while open, so its state resets cleanly on every open. */}
        {open && <FixedEventForm eventType={eventType} onDone={() => setOpen(false)} />}
      </Dialog>
    </>
  );
}

/**
 * Sends the form as an event, then toasts what its rules did and refreshes
 * everything they can change. Both test dialogs share it.
 */
function useSendEvent(onDone: () => void) {
  const toast = useToast();
  const revalidate = useRevalidate();
  const [state, formAction] = useActionState(sendEvent, idleState);

  useEffect(() => {
    if (state.ok) {
      toast.success(state.message ?? "Event recorded.");
      // Rules can move points, prizes, challenges and segments.
      revalidate.members();
      revalidate.segments();
      revalidate.events();
      onDone();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  return [state, formAction] as const;
}

function FixedEventForm({ eventType, onDone }: { eventType: EventType; onDone: () => void }) {
  const { data: members } = useMembers();
  const [memberId, setMemberId] = useState("");
  const [state, formAction] = useSendEvent(onDone);

  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="type" value={eventType.key} />

      <Field label="Member" htmlFor="test-event-member">
        <Select
          id="test-event-member"
          name="memberId"
          value={memberId}
          onChange={(e) => setMemberId(e.target.value)}
          disabled={members === undefined}
        >
          <option value="">{members === undefined ? "Loading members…" : "Choose a member"}</option>
          {(members ?? []).map((m) => (
            <option key={m.id} value={m.id}>
              {memberOptionLabel(m)}
            </option>
          ))}
        </Select>
      </Field>

      <EventAttributeFields attributes={eventType.attributes} />

      {state.error && <ErrorBanner message={state.error} />}
      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="secondary" onClick={onDone}>
          Cancel
        </Button>
        <SubmitButton disabled={!memberId}>Send test event</SubmitButton>
      </div>
    </form>
  );
}

/**
 * Test any event, from the events list: pick one of the program's events,
 * then a member. Both lists come from the program chosen in the sidebar, the
 * same one the rest of the console shows, so the result lands on the member
 * you'd then open.
 */
export function TestEventPickerButton({ eventTypes }: { eventTypes: EventType[] }) {
  const [open, setOpen] = useState(false);
  const activeEventTypes = eventTypes.filter((t) => t.isActive);
  const disabled = activeEventTypes.length === 0;

  return (
    <>
      <Button
        variant="secondary"
        onClick={() => setOpen(true)}
        disabled={disabled}
        title={disabled ? "Define an event and turn it on to test it." : undefined}
      >
        <BoltIcon /> Test event
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Test an event"
        description="Choose an event and a member to send it for. Its rules run right away."
      >
        {open && <PickerEventForm eventTypes={activeEventTypes} onDone={() => setOpen(false)} />}
      </Dialog>
    </>
  );
}

function PickerEventForm({ eventTypes, onDone }: { eventTypes: EventType[]; onDone: () => void }) {
  const { data: members } = useMembers();
  const [typeKey, setTypeKey] = useState("");
  const [memberId, setMemberId] = useState("");
  const [state, formAction] = useSendEvent(onDone);
  const eventType = eventTypes.find((t) => t.key === typeKey);

  return (
    <form action={formAction} className="space-y-4">
      <Field label="Event" htmlFor="test-event-type">
        <Select
          id="test-event-type"
          name="type"
          value={typeKey}
          onChange={(e) => setTypeKey(e.target.value)}
        >
          <option value="">Choose an event</option>
          {eventTypes.map((t) => (
            <option key={t.id} value={t.key}>
              {t.name}
            </option>
          ))}
        </Select>
      </Field>

      <Field label="Member" htmlFor="test-event-member">
        <Select
          id="test-event-member"
          name="memberId"
          value={memberId}
          onChange={(e) => setMemberId(e.target.value)}
          disabled={members === undefined}
        >
          <option value="">{members === undefined ? "Loading members…" : "Choose a member"}</option>
          {(members ?? []).map((m) => (
            <option key={m.id} value={m.id}>
              {memberOptionLabel(m)}
            </option>
          ))}
        </Select>
      </Field>

      {/* Keyed by event so switching events clears the previous one's inputs. */}
      <div key={typeKey} className="space-y-4">
        <EventAttributeFields attributes={eventType?.attributes ?? []} />
      </div>

      {state.error && <ErrorBanner message={state.error} />}
      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="secondary" onClick={onDone}>
          Cancel
        </Button>
        <SubmitButton disabled={!memberId || !eventType}>Send test event</SubmitButton>
      </div>
    </form>
  );
}
