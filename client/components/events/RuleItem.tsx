"use client";

import { Fragment, useTransition } from "react";

import { deleteEventRule, setEventRuleActive } from "@/lib/events/actions";
import { cn } from "@/lib/format";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { EventRule, EventType, RuleEffectType } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { Switch } from "@/components/ui/Switch";
import { useToast } from "@/components/ui/Toast";
import {
  ArrowDownIcon,
  ClockIcon,
  CoinsIcon,
  GiftIcon,
  PencilIcon,
  TagIcon,
  TargetIcon,
  TrashIcon,
  UserIcon,
} from "@/components/ui/icons";
import {
  capitalize,
  conditionFields,
  conditionText,
  effectText,
  type Catalog,
} from "./rules";

const EFFECT_ICONS: Record<RuleEffectType, typeof CoinsIcon> = {
  addPoints: CoinsIcon,
  burnPoints: ArrowDownIcon,
  grantReward: GiftIcon,
  assignChallenge: TargetIcon,
  addChallengeProgress: TargetIcon,
  addToSegment: TagIcon,
  removeFromSegment: TagIcon,
  updateMember: UserIcon,
};

/** One rule, read as IF … THEN … chips, with an on/off switch. */
export function RuleItem({
  rule,
  eventType,
  catalog,
  onEdit,
}: {
  rule: EventRule;
  eventType: EventType;
  catalog: Catalog;
  onEdit: () => void;
}) {
  const toast = useToast();
  const revalidate = useRevalidate();
  const [pending, startTransition] = useTransition();
  const fields = conditionFields(eventType, catalog);

  const toggle = (isActive: boolean) =>
    startTransition(async () => {
      const result = await setEventRuleActive(eventType.id, rule.id, isActive);
      if (result.ok) {
        toast.info(isActive ? `"${rule.name}" is on.` : `"${rule.name}" is paused.`);
        revalidate.eventTypes();
      } else {
        toast.error(result.error ?? "Couldn't change the rule.");
      }
    });

  return (
    <li className="px-5 py-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1.5">
          <span className={cn(pending && "pointer-events-none opacity-60")}>
            <Switch
              checked={rule.isActive}
              label={rule.isActive ? `Pause ${rule.name}` : `Turn on ${rule.name}`}
              onChange={toggle}
            />
          </span>
          <p className="font-medium text-foreground">{rule.name}</p>
          {!rule.isActive && <Badge tone="neutral">Paused</Badge>}
          {rule.limitPerMember !== null && (
            <Badge tone="neutral">
              <ClockIcon className="text-[0.8125rem]" />
              {rule.limitPerMember === 1 ? "Once per member" : `Up to ${rule.limitPerMember} per member`}
            </Badge>
          )}
        </div>
        <div className="-mr-2 -mt-1 flex shrink-0 items-center gap-1">
          <Button variant="ghost" size="icon" aria-label={`Edit ${rule.name}`} onClick={onEdit}>
            <PencilIcon />
          </Button>
          <ConfirmButton
            trigger={
              <Button variant="ghost" size="icon" aria-label={`Delete ${rule.name}`}>
                <TrashIcon />
              </Button>
            }
            title={`Delete "${rule.name}"?`}
            description="New events stop triggering it. Events already received keep what they earned."
            confirmLabel="Delete rule"
            action={() => deleteEventRule(eventType.id, rule.id)}
            onSuccess={() => revalidate.eventTypes()}
          />
        </div>
      </div>

      <div className={cn("mt-3 space-y-2", !rule.isActive && "opacity-60")}>
        <ClauseLine keyword="If">
          {rule.conditions.length === 0 ? (
            <span className="text-muted">Always, on every event</span>
          ) : (
            rule.conditions.map((condition, i) => (
              <Fragment key={i}>
                {i > 0 && <span className="text-faint">and</span>}
                <span className="rounded-md border border-line bg-surface-2 px-2 py-0.5 text-foreground">
                  {capitalize(conditionText(condition, fields))}
                </span>
              </Fragment>
            ))
          )}
        </ClauseLine>
        <ClauseLine keyword="Then">
          {rule.effects.map((effect, i) => {
            const Icon = EFFECT_ICONS[effect.type];
            return (
              <Fragment key={i}>
                {i > 0 && <span className="text-faint">and</span>}
                <span className="inline-flex items-center gap-1.5 rounded-md bg-primary-subtle px-2 py-0.5 text-primary-subtle-fg">
                  <Icon className="shrink-0" />
                  {capitalize(effectText(effect, eventType, catalog))}
                </span>
              </Fragment>
            );
          })}
        </ClauseLine>
      </div>
    </li>
  );
}

function ClauseLine({ keyword, children }: { keyword: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <span className="w-10 shrink-0 pt-0.5 text-[0.6875rem] font-semibold uppercase tracking-wide text-faint">
        {keyword}
      </span>
      <div className="flex min-w-0 flex-wrap items-center gap-1.5 text-[0.8125rem]">{children}</div>
    </div>
  );
}
