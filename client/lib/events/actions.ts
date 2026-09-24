"use server";

import { randomUUID } from "node:crypto";
import { revalidatePath } from "next/cache";

import type { ActionState } from "@/lib/action-state";
import { ApiError, apiRequest } from "@/lib/api";
import type { EventRuleInput, EventType, EventTypeInput, Member, MemberEvent } from "@/lib/types";

/**
 * Event types, their rules, and sending an event by hand from a member's page.
 * The rule builder holds its state in the browser, so these take plain objects
 * rather than FormData; the API validates every rule before saving it.
 */

function fail(error: unknown): ActionState {
  if (error instanceof ApiError) return { ok: false, error: error.message };
  console.error("[action] unexpected error:", error);
  return { ok: false, error: "Something went wrong. Please try again." };
}

function refreshEvents(): void {
  revalidatePath("/admin/events", "layout");
}

// ── Event types ──────────────────────────────────────────────────────────────

export async function createEventType(
  input: EventTypeInput,
): Promise<ActionState & { id?: string }> {
  if (!input.name.trim()) return { ok: false, error: "Name is required." };
  try {
    const created = await apiRequest<EventType>("/event-types", { method: "POST", json: input });
    refreshEvents();
    return { ok: true, message: "Event created. Add a rule, then turn it on.", id: created.id };
  } catch (e) {
    return fail(e);
  }
}

export async function updateEventType(id: string, input: EventTypeInput): Promise<ActionState> {
  if (!input.name.trim()) return { ok: false, error: "Name is required." };
  try {
    await apiRequest(`/event-types/${id}`, { method: "PATCH", json: input });
    refreshEvents();
    return { ok: true, message: "Event saved." };
  } catch (e) {
    return fail(e);
  }
}

export async function setEventTypeActive(id: string, isActive: boolean): Promise<ActionState> {
  try {
    await apiRequest(`/event-types/${id}`, { method: "PATCH", json: { isActive } });
    refreshEvents();
    return {
      ok: true,
      message: isActive ? "Event turned on." : "Event turned off. Incoming events are rejected.",
    };
  } catch (e) {
    return fail(e);
  }
}

export async function deleteEventType(id: string): Promise<ActionState> {
  try {
    await apiRequest(`/event-types/${id}`, { method: "DELETE" });
    refreshEvents();
    return { ok: true, message: "Event deleted." };
  } catch (e) {
    return fail(e);
  }
}

// ── Rules ────────────────────────────────────────────────────────────────────

/** Create a rule when `ruleId` is null, otherwise replace that rule. */
export async function saveEventRule(
  eventTypeId: string,
  ruleId: string | null,
  input: EventRuleInput,
): Promise<ActionState> {
  if (!input.name.trim()) return { ok: false, error: "Give the rule a name." };
  try {
    await apiRequest(
      ruleId ? `/event-types/${eventTypeId}/rules/${ruleId}` : `/event-types/${eventTypeId}/rules`,
      { method: ruleId ? "PATCH" : "POST", json: input },
    );
    refreshEvents();
    return { ok: true, message: ruleId ? "Rule saved." : "Rule created." };
  } catch (e) {
    return fail(e);
  }
}

export async function setEventRuleActive(
  eventTypeId: string,
  ruleId: string,
  isActive: boolean,
): Promise<ActionState> {
  try {
    await apiRequest(`/event-types/${eventTypeId}/rules/${ruleId}`, {
      method: "PATCH",
      json: { isActive },
    });
    refreshEvents();
    return { ok: true, message: isActive ? "Rule turned on." : "Rule paused." };
  } catch (e) {
    return fail(e);
  }
}

export async function deleteEventRule(eventTypeId: string, ruleId: string): Promise<ActionState> {
  try {
    await apiRequest(`/event-types/${eventTypeId}/rules/${ruleId}`, { method: "DELETE" });
    refreshEvents();
    return { ok: true, message: "Rule deleted." };
  } catch (e) {
    return fail(e);
  }
}

// ── Sending an event ─────────────────────────────────────────────────────────

/**
 * Send an event for a member from the console, as an integration would.
 *
 * Attribute inputs are named `attr.<key>` and sent as typed text; the API
 * coerces each one against the event's definition. Blank inputs are left out.
 * A fresh `eventId` makes the call safe to retry: `apiRequest` retries on a
 * server error, and the API runs an event's rules only once per id.
 */
export async function sendEvent(_prev: ActionState, fd: FormData): Promise<ActionState> {
  const memberId = String(fd.get("memberId") ?? "");
  const type = String(fd.get("type") ?? "");
  if (!type) return { ok: false, error: "Choose an event." };

  const attributes: Record<string, string> = {};
  for (const [name, value] of fd.entries()) {
    if (name.startsWith("attr.") && typeof value === "string" && value.trim()) {
      attributes[name.slice("attr.".length)] = value.trim();
    }
  }

  try {
    const event = await apiRequest<MemberEvent>("/events", {
      method: "POST",
      json: { memberId, type, attributes, eventId: `console-${randomUUID()}` },
    });
    revalidatePath(`/admin/members/${memberId}`);
    const applied = event.effects.filter((e) => !e.skipped).map((e) => e.summary);
    const skipped = event.effects.length - applied.length;
    if (!event.effects.length) return { ok: true, message: "Event recorded. No rules matched." };
    return {
      ok: true,
      message: `Event recorded. ${applied.join(". ") || "Nothing applied"}${
        skipped ? ` (${skipped} skipped)` : ""
      }.`,
    };
  } catch (e) {
    return fail(e);
  }
}

// ── Testing an event from the events pages (any program, any member) ───────

/**
 * Every member in `programId`, for the test-event member picker. Members are
 * one row per program - a demo's "new program opens holding everyone already"
 * (see lib/programs/actions.ts) - so a member chosen under one program is a
 * different id than the same person under another.
 */
export async function listMembersForProgram(programId: string): Promise<Member[]> {
  return apiRequest<Member[]>("/members", { query: { limit: 1000 }, programId });
}

/** Every event type defined in `programId`, for the test-event event picker. */
export async function listEventTypesForProgram(programId: string): Promise<EventType[]> {
  return apiRequest<EventType[]>("/event-types", { programId });
}

/**
 * Test an event for any member, from a single event's page or the events
 * list, rather than a member's own page.
 *
 * `programId` is only present when the caller offers a program picker (the
 * events-list dialog, which also re-scopes its event and member pickers to
 * it). Left blank, it defaults to the console's active program - what the
 * single-event dialog wants, since that event only exists in the program
 * already on screen.
 */
export async function testEvent(_prev: ActionState, fd: FormData): Promise<ActionState> {
  const programId = String(fd.get("programId") ?? "").trim() || undefined;
  const memberId = String(fd.get("memberId") ?? "");
  const type = String(fd.get("type") ?? "");
  if (!memberId) return { ok: false, error: "Choose a member." };
  if (!type) return { ok: false, error: "Choose an event." };

  const attributes: Record<string, string> = {};
  for (const [name, value] of fd.entries()) {
    if (name.startsWith("attr.") && typeof value === "string" && value.trim()) {
      attributes[name.slice("attr.".length)] = value.trim();
    }
  }

  try {
    const event = await apiRequest<MemberEvent>("/events", {
      method: "POST",
      programId,
      json: { memberId, type, attributes, eventId: `console-${randomUUID()}` },
    });
    const applied = event.effects.filter((e) => !e.skipped).map((e) => e.summary);
    const skipped = event.effects.length - applied.length;
    if (!event.effects.length) return { ok: true, message: "Event recorded. No rules matched." };
    return {
      ok: true,
      message: `Event recorded. ${applied.join(". ") || "Nothing applied"}${
        skipped ? ` (${skipped} skipped)` : ""
      }.`,
    };
  } catch (e) {
    return fail(e);
  }
}
