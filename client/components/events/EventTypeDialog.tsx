"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { ATTRIBUTE_TYPES, ATTRIBUTE_TYPE_LABELS, previewKey } from "@/lib/custom-attributes";
import { createEventType, updateEventType } from "@/lib/events/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { EventType, EventTypeInput, MemberAttributeType } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Field, Input, Select, Textarea } from "@/components/ui/Field";
import { Dialog } from "@/components/ui/Dialog";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useToast } from "@/components/ui/Toast";
import { PlusIcon, XIcon } from "@/components/ui/icons";

/** Define a new event type, or edit one. Keys and attribute types are fixed
 *  once created, the same rule member attributes follow. */
export function EventTypeDialog({
  open,
  onClose,
  eventType,
}: {
  open: boolean;
  onClose: () => void;
  /** Omit to create a new event type. */
  eventType?: EventType;
}) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={eventType ? "Edit event" : "New event"}
      description="Something a member does that your systems report, such as placing an order."
      size="lg"
    >
      <EventTypeForm eventType={eventType} onDone={onClose} />
    </Dialog>
  );
}

interface DraftAttribute {
  /** Set for attributes that already exist: their key and type are fixed. */
  key?: string;
  label: string;
  type: MemberAttributeType;
  options: string;
}

function EventTypeForm({ eventType, onDone }: { eventType?: EventType; onDone: () => void }) {
  const toast = useToast();
  const router = useRouter();
  const revalidate = useRevalidate();
  const [pending, startTransition] = useTransition();

  const [name, setName] = useState(eventType?.name ?? "");
  const [description, setDescription] = useState(eventType?.description ?? "");
  const [attributes, setAttributes] = useState<DraftAttribute[]>(
    eventType?.attributes.map((a) => ({
      key: a.key,
      label: a.label,
      type: a.type,
      options: (a.options ?? []).join(", "),
    })) ?? [],
  );
  const [error, setError] = useState<string | null>(null);

  const key = eventType?.key ?? previewKey(name);

  const updateAttribute = (index: number, patch: Partial<DraftAttribute>) =>
    setAttributes((list) => list.map((a, i) => (i === index ? { ...a, ...patch } : a)));

  const save = () => {
    if (!name.trim() || !key) {
      setError("Give the event a name that starts with a letter.");
      return;
    }
    if (attributes.some((a) => !a.label.trim())) {
      setError("Every attribute needs a label.");
      return;
    }
    const input: EventTypeInput = {
      name: name.trim(),
      description: description.trim() || null,
      // New events start off, so they can be set up before integrations
      // hit them. Editing leaves the on/off state alone.
      ...(eventType ? {} : { isActive: false }),
      attributes: attributes.map((a) => ({
        ...(a.key ? { key: a.key } : {}),
        label: a.label.trim(),
        type: a.type,
        options:
          a.type === "select"
            ? a.options.split(",").map((o) => o.trim()).filter(Boolean)
            : null,
      })),
    };
    setError(null);
    startTransition(async () => {
      if (eventType) {
        const result = await updateEventType(eventType.id, input);
        if (!result.ok) return setError(result.error ?? "Couldn't save the event.");
        toast.success(result.message ?? "Event saved.");
        revalidate.eventTypes();
        onDone();
        return;
      }
      const result = await createEventType(input);
      if (!result.ok) return setError(result.error ?? "Couldn't create the event.");
      toast.success(result.message ?? "Event created.");
      revalidate.eventTypes();
      onDone();
      if (result.id) router.push(`/admin/events/${result.id}`);
    });
  };

  return (
    <div className="space-y-4">
      <Field
        label="Name"
        htmlFor="event-name"
        help={
          eventType
            ? `API key: ${key}. It can't change once created.`
            : `API key: ${key || "…"}. Your system sends this as "type".`
        }
      >
        <Input
          id="event-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Order placed"
          autoFocus
        />
      </Field>

      <Field label="Description" htmlFor="event-description" hint="Optional">
        <Textarea
          id="event-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Who sends it, and when"
        />
      </Field>

      <div>
        <p className="mb-1 text-[0.8125rem] font-medium text-foreground">Attributes</p>
        <p className="mb-2 text-xs text-faint">
          Data your system sends with the event. Rules can check these values or copy them onto the member.
        </p>
        <div className="space-y-2">
          {attributes.map((attribute, i) => (
            <div key={i} className="rounded-lg border border-line p-2">
              <div className="grid gap-2 sm:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_auto]">
                <Input
                  aria-label="Attribute label"
                  value={attribute.label}
                  onChange={(e) => updateAttribute(i, { label: e.target.value })}
                  placeholder="e.g. Amount"
                />
                <Select
                  aria-label="Attribute type"
                  value={attribute.type}
                  disabled={attribute.key !== undefined}
                  onChange={(e) => updateAttribute(i, { type: e.target.value as MemberAttributeType })}
                >
                  {ATTRIBUTE_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {ATTRIBUTE_TYPE_LABELS[t]}
                    </option>
                  ))}
                </Select>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Remove attribute"
                  className="justify-self-end"
                  onClick={() => setAttributes((list) => list.filter((_, j) => j !== i))}
                >
                  <XIcon />
                </Button>
              </div>
              {attribute.type === "select" && (
                <Input
                  aria-label="Dropdown options"
                  className="mt-2"
                  value={attribute.options}
                  onChange={(e) => updateAttribute(i, { options: e.target.value })}
                  placeholder="Options, separated by commas"
                />
              )}
              <p className="mt-1.5 px-1 font-mono text-[0.6875rem] text-faint">
                {attribute.key ?? (previewKey(attribute.label) || "key")}
              </p>
            </div>
          ))}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 mt-1"
          onClick={() => setAttributes((list) => [...list, { label: "", type: "text", options: "" }])}
        >
          <PlusIcon /> Add attribute
        </Button>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="flex justify-end gap-2 pt-1">
        <Button variant="secondary" onClick={onDone} disabled={pending}>
          Cancel
        </Button>
        <Button onClick={save} loading={pending}>
          {eventType ? "Save changes" : "Create event"}
        </Button>
      </div>
    </div>
  );
}
