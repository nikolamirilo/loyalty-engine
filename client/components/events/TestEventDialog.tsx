"use client";

import { useActionState, useEffect, useState } from "react";
import useSWR from "swr";

import { idleState } from "@/lib/action-state";
import {
  listEventTypesForProgram,
  listMembersForProgram,
  testEvent,
} from "@/lib/events/actions";
import { useMembers, usePrograms } from "@/lib/swr/hooks";
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

function FixedEventForm({ eventType, onDone }: { eventType: EventType; onDone: () => void }) {
  const toast = useToast();
  const revalidate = useRevalidate();
  const { data: members } = useMembers();
  const [memberId, setMemberId] = useState("");
  const [state, formAction] = useActionState(testEvent, idleState);

  useEffect(() => {
    if (state.ok) {
      toast.success(state.message ?? "Event recorded.");
      revalidate.members();
      revalidate.segments();
      onDone();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

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
 * Test any event, from the events list: pick a program, then which of its
 * events to test, then a member - each list re-scoped to whichever program is
 * currently chosen, so the three never end up mismatched.
 */
export function TestEventPickerButton({ eventTypes }: { eventTypes: EventType[] }) {
  const [open, setOpen] = useState(false);
  // Best-effort: whether the console's own active program has anything to
  // test, so the button doesn't invite opening an empty dialog. The dialog
  // itself re-fetches per program once open.
  const disabled = eventTypes.filter((t) => t.isActive).length === 0;

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
        description="Choose a program, a member, and an event to send. Its rules run right away."
      >
        {open && <PickerEventForm onDone={() => setOpen(false)} />}
      </Dialog>
    </>
  );
}

function PickerEventForm({ onDone }: { onDone: () => void }) {
  const toast = useToast();
  const revalidate = useRevalidate();
  const { data: programs } = usePrograms();

  const [chosenProgramId, setChosenProgramId] = useState("");
  const [typeKey, setTypeKey] = useState("");
  const [memberId, setMemberId] = useState("");

  // Falls back to the default program once the list loads, the way
  // `SendEventFields` falls back to the first event - no dialog left
  // pointed at nothing just because the admin hasn't touched this yet.
  const defaultProgram = programs ? (programs.find((p) => p.isDefault) ?? programs[0]) : undefined;
  const programId = chosenProgramId || defaultProgram?.id || "";

  // Re-scoped to whichever program is chosen - an event or a member from one
  // program is meaningless in another - and cleared together whenever the
  // program changes, since a previous pick may no longer exist here.
  const { data: eventTypes, error: eventTypesError } = useSWR(
    programId ? ["test-event-types", programId] : null,
    () => listEventTypesForProgram(programId),
  );
  const { data: members, error: membersError } = useSWR(
    programId ? ["test-event-members", programId] : null,
    () => listMembersForProgram(programId),
  );
  const loadingLists = programId !== "" && (eventTypes === undefined || members === undefined);
  const listsError = programId ? (eventTypesError ?? membersError) : undefined;
  useEffect(() => {
    if (listsError) toast.error("Couldn't load that program's events and members.");
    // Only react to a change in the error itself.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listsError]);

  const activeEventTypes = (eventTypes ?? []).filter((t) => t.isActive);
  const eventType = activeEventTypes.find((t) => t.key === typeKey);

  const selectProgram = (id: string) => {
    setChosenProgramId(id);
    setTypeKey("");
    setMemberId("");
  };

  const [state, formAction] = useActionState(testEvent, idleState);
  useEffect(() => {
    if (state.ok) {
      toast.success(state.message ?? "Event recorded.");
      revalidate.members();
      revalidate.segments();
      onDone();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="programId" value={programId} />

      <Field label="Program" htmlFor="test-event-program">
        <Select
          id="test-event-program"
          value={programId}
          onChange={(e) => selectProgram(e.target.value)}
          disabled={programs === undefined}
        >
          {(programs ?? []).map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </Select>
      </Field>

      <Field label="Event" htmlFor="test-event-type">
        <Select
          id="test-event-type"
          name="type"
          value={typeKey}
          onChange={(e) => setTypeKey(e.target.value)}
          disabled={loadingLists || activeEventTypes.length === 0}
        >
          <option value="">
            {loadingLists ? "Loading…" : activeEventTypes.length === 0 ? "No active events" : "Choose an event"}
          </option>
          {activeEventTypes.map((t) => (
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
          disabled={loadingLists || (members ?? []).length === 0}
        >
          <option value="">{loadingLists ? "Loading…" : "Choose a member"}</option>
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
        <SubmitButton disabled={!programId || !memberId || !eventType}>Send test event</SubmitButton>
      </div>
    </form>
  );
}
