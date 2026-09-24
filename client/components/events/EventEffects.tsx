import type { AppliedEffect, CustomAttributeValue, EventType, MemberEvent } from "@/lib/types";
import { CheckCircleIcon } from "@/components/ui/icons";

/**
 * What a received event's rules did, one line per effect. Shared by a
 * member's events card and the program-wide event log.
 */
export function EventEffects({ effects }: { effects: AppliedEffect[] }) {
  if (effects.length === 0) {
    return <span className="text-[0.8125rem] text-muted">No rules matched</span>;
  }
  return (
    <ul className="space-y-1 text-[0.8125rem]">
      {effects.map((effect, i) => (
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
  );
}

/**
 * An event's attributes as one line, e.g. "Order total 45 · Channel App".
 * Events store attribute keys; this shows the labels the admin defined, when
 * the event type still exists.
 */
export function eventDetails(event: MemberEvent, eventTypes: EventType[] | undefined): string {
  const attributes = eventTypes?.find((t) => t.key === event.type)?.attributes;
  return Object.entries(event.attributes)
    .map(([key, value]) => `${attributes?.find((a) => a.key === key)?.label ?? key} ${display(value)}`)
    .join(" · ");
}

function display(value: CustomAttributeValue): string {
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return value === null ? "-" : String(value);
}
