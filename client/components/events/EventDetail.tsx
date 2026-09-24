"use client";

import { useMemo, useState, useTransition } from "react";
import Link from "next/link";

import { ATTRIBUTE_TYPE_LABELS } from "@/lib/custom-attributes";
import { deleteEventType, setEventTypeActive } from "@/lib/events/actions";
import { cn } from "@/lib/format";
import { ApiError } from "@/lib/swr/error";
import {
  useChallenges,
  useEventType,
  useMemberAttributes,
  useRewards,
  useSegments,
  useTiers,
} from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { EventRule, EventType } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { Switch } from "@/components/ui/Switch";
import { useToast } from "@/components/ui/Toast";
import {
  AlertTriangleIcon,
  BoltIcon,
  ChevronRightIcon,
  CopyIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
} from "@/components/ui/icons";
import { EventTypeDialog } from "./EventTypeDialog";
import { RuleEditorDialog } from "./RuleEditorDialog";
import { RuleItem } from "./RuleItem";
import { TestEventButton } from "./TestEventDialog";
import { curlExample, type Catalog } from "./rules";

/** One event type: its rules on the left, its shape and how to send it on the right. */
export function EventDetail({ id }: { id: string }) {
  const toast = useToast();
  const revalidate = useRevalidate();
  const { data: eventType, error, mutate } = useEventType(id);
  const { data: rewards } = useRewards();
  const { data: challenges } = useChallenges();
  const { data: segments } = useSegments();
  const { data: tiers } = useTiers();
  const { data: memberAttributes } = useMemberAttributes();
  const [editingEvent, setEditingEvent] = useState(false);
  const [ruleDialog, setRuleDialog] = useState<{ open: boolean; rule?: EventRule }>({ open: false });

  const catalog = useMemo<Catalog>(
    () => ({
      rewards: rewards ?? [],
      challenges: challenges ?? [],
      segments: segments ?? [],
      tiers: tiers ?? [],
      memberAttributes: memberAttributes ?? [],
    }),
    [rewards, challenges, segments, tiers, memberAttributes],
  );

  // The rule builder's pickers read these lists, so it opens only once they're in.
  const catalogReady = [rewards, challenges, segments, tiers, memberAttributes].every(Boolean);
  const openRule = (rule?: EventRule) => {
    if (catalogReady) setRuleDialog({ open: true, rule });
  };

  if (error && !eventType) {
    const missing = error instanceof ApiError && error.status === 404;
    return (
      <div className="space-y-6">
        <BackLink />
        <Card>
          <EmptyState
            icon={missing ? <BoltIcon /> : <AlertTriangleIcon />}
            title={missing ? "Event not found" : "Couldn't load this event"}
            description={missing ? "It may have been deleted." : (error as Error).message}
            action={
              missing ? undefined : (
                <Button variant="secondary" onClick={() => mutate()}>
                  Retry
                </Button>
              )
            }
          />
        </Card>
      </div>
    );
  }
  if (!eventType) return <EventDetailSkeleton />;

  const copy = async (text: string, what: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${what} copied.`);
    } catch {
      toast.error(`Couldn't copy ${what.toLowerCase()}.`);
    }
  };

  return (
    <div className="space-y-6">
      <BackLink />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-accent-violet/15 text-xl text-accent-violet">
            <BoltIcon />
          </span>
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">{eventType.name}</h1>
            {eventType.description && <p className="mt-1 text-sm text-muted">{eventType.description}</p>}
            <button
              type="button"
              onClick={() => copy(eventType.key, "API key")}
              className="mt-2 inline-flex cursor-pointer items-center gap-1.5 rounded-md bg-surface-2 px-2 py-1 font-mono text-xs text-muted transition-colors hover:text-foreground"
            >
              {eventType.key}
              <CopyIcon />
            </button>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <ActiveToggle eventType={eventType} />
          <TestEventButton eventType={eventType} />
          <Button variant="secondary" onClick={() => setEditingEvent(true)}>
            <PencilIcon /> Edit event
          </Button>
          <ConfirmButton
            trigger={
              <Button variant="ghost" size="icon" aria-label={`Delete ${eventType.name}`}>
                <TrashIcon />
              </Button>
            }
            title={`Delete "${eventType.name}"?`}
            description="Its rules are deleted too. Events already received stay in each member's history."
            confirmLabel="Delete event"
            redirectTo="/admin/events"
            action={() => deleteEventType(eventType.id)}
            onSuccess={() => revalidate.eventTypes()}
          />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="overflow-hidden lg:col-span-2">
          <CardHeader
            title="Rules"
            description="Every active rule whose conditions match runs. Their order doesn't matter."
            action={
              <Button size="sm" onClick={() => openRule()} loading={!catalogReady}>
                <PlusIcon /> New rule
              </Button>
            }
          />
          {!eventType.isActive && (
            <div className="flex items-start gap-2 border-b border-line bg-warning-subtle px-5 py-2.5 text-[0.8125rem] text-warning-fg">
              <AlertTriangleIcon className="mt-0.5 shrink-0" />
              This event is off, so incoming events are rejected and no rules run. Turn it on at the
              top when it&apos;s ready.
            </div>
          )}
          {eventType.rules.length === 0 ? (
            <EmptyState
              icon={<BoltIcon />}
              title="No rules yet"
              description={`${eventType.isActive ? "Events are still recorded. " : ""}Add a rule to decide what "${eventType.name}" earns.`}
              action={
                <Button onClick={() => openRule()} loading={!catalogReady}>
                  <PlusIcon /> New rule
                </Button>
              }
            />
          ) : (
            <ul className="divide-y divide-line">
              {eventType.rules.map((rule) => (
                <RuleItem
                  key={rule.id}
                  rule={rule}
                  eventType={eventType}
                  catalog={catalog}
                  onEdit={() => openRule(rule)}
                />
              ))}
            </ul>
          )}
        </Card>

        <div className="space-y-6">
          <Card className="overflow-hidden">
            <CardHeader title="Attributes" description="Data sent with each event" />
            {eventType.attributes.length === 0 ? (
              <p className="px-5 py-4 text-[0.8125rem] text-muted">
                None. The event only says which member it was.
              </p>
            ) : (
              <ul className="divide-y divide-line">
                {eventType.attributes.map((a) => (
                  <li key={a.key} className="flex items-center justify-between gap-3 px-5 py-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground">{a.label}</p>
                      <p className="font-mono text-xs text-faint">{a.key}</p>
                    </div>
                    <Badge tone="neutral">{ATTRIBUTE_TYPE_LABELS[a.type]}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card className="overflow-hidden">
            <CardHeader
              title="Send this event"
              description="POST it from your system. The response lists what the rules did."
              action={
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Copy request"
                  onClick={() => copy(curlExample(eventType), "Request")}
                >
                  <CopyIcon />
                </Button>
              }
            />
            <pre className="overflow-x-auto bg-surface-2 px-5 py-4 font-mono text-xs leading-relaxed text-foreground">
              {curlExample(eventType)}
            </pre>
          </Card>
        </div>
      </div>

      <EventTypeDialog open={editingEvent} onClose={() => setEditingEvent(false)} eventType={eventType} />
      <RuleEditorDialog
        open={ruleDialog.open}
        onClose={() => setRuleDialog({ open: false })}
        eventType={eventType}
        catalog={catalog}
        rule={ruleDialog.rule}
      />
    </div>
  );
}

/** Turns the event on or off right away: off means the API rejects it. */
function ActiveToggle({ eventType }: { eventType: EventType }) {
  const toast = useToast();
  const revalidate = useRevalidate();
  const [pending, startTransition] = useTransition();

  const toggle = (isActive: boolean) =>
    startTransition(async () => {
      const result = await setEventTypeActive(eventType.id, isActive);
      if (result.ok) {
        toast.info(result.message ?? (isActive ? "Event turned on." : "Event turned off."));
        revalidate.eventTypes();
      } else {
        toast.error(result.error ?? "Couldn't change the event.");
      }
    });

  return (
    <div className={cn("mr-2 flex items-center gap-2", pending && "pointer-events-none opacity-60")}>
      <Switch checked={eventType.isActive} label="Active" onChange={toggle} />
      <span className="text-sm font-medium text-foreground">
        {eventType.isActive ? "Active" : "Inactive"}
      </span>
    </div>
  );
}

function BackLink() {
  return (
    <Link
      href="/admin/events"
      className="inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-foreground"
    >
      <ChevronRightIcon className="rotate-180 text-base" />
      All events
    </Link>
  );
}

function EventDetailSkeleton() {
  return (
    <div className="space-y-6">
      <BackLink />
      <div className="flex items-start gap-3">
        <Skeleton className="h-11 w-11 rounded-lg" />
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="space-y-4 p-5 lg:col-span-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-6 w-full" />
            </div>
          ))}
        </Card>
        <Card className="space-y-3 p-5">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </Card>
      </div>
    </div>
  );
}
