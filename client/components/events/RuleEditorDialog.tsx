"use client";

import { useMemo, useState, useTransition } from "react";

import { saveEventRule } from "@/lib/events/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import type {
  EventAttribute,
  EventRule,
  EventType,
  RuleEffect,
  RuleEffectType,
  RuleOperator,
} from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Field, Input, Select } from "@/components/ui/Field";
import { useToast } from "@/components/ui/Toast";
import { BoltIcon, PlusIcon, SparklesIcon, XIcon } from "@/components/ui/icons";
import {
  EFFECT_TYPES,
  conditionFields,
  conditionFor,
  copyableAttributes,
  operatorLabel,
  operatorsFor,
  ruleSentence,
  updatableFields,
  valueToInput,
  type Catalog,
  type FieldDef,
} from "./rules";

/**
 * The rule builder: WHEN the event happens, IF all conditions match, THEN run
 * every effect. Everything is a dropdown or a short input, and the plain-words
 * preview says what the rule will do before it is saved.
 */
export function RuleEditorDialog({
  open,
  onClose,
  eventType,
  catalog,
  rule,
}: {
  open: boolean;
  onClose: () => void;
  eventType: EventType;
  catalog: Catalog;
  /** Omit to create a new rule. */
  rule?: EventRule;
}) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={rule ? "Edit rule" : "New rule"}
      description={`Decide what a "${eventType.name}" event does for the member.`}
      size="lg"
    >
      {/* Mounted only while open, so the draft resets on every open. */}
      <RuleEditorBody eventType={eventType} catalog={catalog} rule={rule} onDone={onClose} />
    </Dialog>
  );
}

// ── draft state: inputs hold strings, converted on save ─────────────────────

interface DraftCondition {
  field: string;
  operator: RuleOperator;
  value: string;
}

interface DraftFieldUpdate {
  field: string;
  /** Event attribute key to copy from; "" means use `value`. */
  fromAttribute: string;
  value: string;
}

interface DraftEffect {
  type: RuleEffectType;
  points: string;
  /** Event attribute key the points or progress come from; "" means fixed. */
  fromAttribute: string;
  rewardId: string;
  challengeId: string;
  amount: string;
  segmentId: string;
  fields: DraftFieldUpdate[];
}

function fieldUpdateFor(field: FieldDef | undefined): DraftFieldUpdate {
  return { field: field?.value ?? "", fromAttribute: "", value: field?.options?.[0]?.value ?? "" };
}

function newDraftEffect(type: RuleEffectType, catalog: Catalog): DraftEffect {
  return {
    type,
    points: "10",
    fromAttribute: "",
    rewardId: catalog.rewards[0]?.id ?? "",
    challengeId: catalog.challenges[0]?.id ?? "",
    amount: "1",
    segmentId: catalog.segments[0]?.id ?? "",
    fields: [fieldUpdateFor(updatableFields(catalog)[0])],
  };
}

function toDraft(effect: RuleEffect, catalog: Catalog): DraftEffect {
  const draft = newDraftEffect(effect.type, catalog);
  switch (effect.type) {
    case "addPoints":
    case "burnPoints":
      return {
        ...draft,
        points: effect.points === null ? draft.points : String(effect.points),
        fromAttribute: effect.fromAttribute ?? "",
      };
    case "grantReward":
      return { ...draft, rewardId: effect.rewardId };
    case "assignChallenge":
      return { ...draft, challengeId: effect.challengeId };
    case "addChallengeProgress":
      return {
        ...draft,
        challengeId: effect.challengeId,
        amount: effect.amount === null ? draft.amount : String(effect.amount),
        fromAttribute: effect.fromAttribute ?? "",
      };
    case "addToSegment":
    case "removeFromSegment":
      return { ...draft, segmentId: effect.segmentId };
    case "updateMember":
      return {
        ...draft,
        fields: effect.fields.map((f) => ({
          field: f.field,
          fromAttribute: f.fromAttribute ?? "",
          value: valueToInput(f.value),
        })),
      };
  }
}

function fromDraft(draft: DraftEffect): RuleEffect {
  switch (draft.type) {
    case "addPoints":
    case "burnPoints":
      return {
        type: draft.type,
        points: draft.fromAttribute ? null : Number.parseInt(draft.points, 10) || 0,
        fromAttribute: draft.fromAttribute || null,
      };
    case "grantReward":
      return { type: "grantReward", rewardId: draft.rewardId };
    case "assignChallenge":
      return { type: "assignChallenge", challengeId: draft.challengeId };
    case "addChallengeProgress":
      return {
        type: "addChallengeProgress",
        challengeId: draft.challengeId,
        amount: draft.fromAttribute ? null : Number.parseInt(draft.amount, 10) || 0,
        fromAttribute: draft.fromAttribute || null,
      };
    case "addToSegment":
    case "removeFromSegment":
      return { type: draft.type, segmentId: draft.segmentId };
    case "updateMember":
      return {
        type: "updateMember",
        fields: draft.fields.map((f) => ({
          field: f.field,
          fromAttribute: f.fromAttribute || null,
          value: f.fromAttribute || f.value === "" ? null : f.value,
        })),
      };
  }
}

/** Quick checks so obvious gaps don't need a round trip. The API re-checks
 *  everything, including that the reward, challenge or segment exists. */
function validate(name: string, conditions: DraftCondition[], effects: DraftEffect[]): string | null {
  if (!name.trim()) return "Give the rule a name.";
  if (conditions.some((c) => !c.value.trim())) return "Fill in a value for every condition.";
  if (!effects.length) return "Add at least one effect, otherwise the rule does nothing.";
  for (const effect of effects) {
    const usesPoints = effect.type === "addPoints" || effect.type === "burnPoints";
    if (usesPoints && !effect.fromAttribute && !(Number.parseInt(effect.points, 10) > 0))
      return "Points must be a whole number above 0.";
    if (effect.type === "grantReward" && !effect.rewardId) return "Create a reward first, then pick it here.";
    if ((effect.type === "addChallengeProgress" || effect.type === "assignChallenge") && !effect.challengeId)
      return "Create a challenge first, then pick it here.";
    if (
      effect.type === "addChallengeProgress" &&
      !effect.fromAttribute &&
      !(Number.parseInt(effect.amount, 10) > 0)
    )
      return "Challenge progress must be a whole number above 0.";
    if ((effect.type === "addToSegment" || effect.type === "removeFromSegment") && !effect.segmentId)
      return "Create a segment first, then pick it here.";
    if (effect.type === "updateMember" && !effect.fields.length) return "Choose at least one member field to set.";
    if (
      effect.type === "updateMember" &&
      effect.fields.some((f) => f.field === "member.name" && !f.fromAttribute && !f.value.trim())
    )
      return "A member's name can't be set to empty.";
  }
  return null;
}

function RuleEditorBody({
  eventType,
  catalog,
  rule,
  onDone,
}: {
  eventType: EventType;
  catalog: Catalog;
  rule?: EventRule;
  onDone: () => void;
}) {
  const toast = useToast();
  const revalidate = useRevalidate();
  const [pending, startTransition] = useTransition();
  const fields = useMemo(() => conditionFields(eventType, catalog), [eventType, catalog]);

  const [name, setName] = useState(rule?.name ?? "");
  const [conditions, setConditions] = useState<DraftCondition[]>(
    () => rule?.conditions.map((c) => ({ ...c, value: valueToInput(c.value) })) ?? [],
  );
  const [effects, setEffects] = useState<DraftEffect[]>(() =>
    rule ? rule.effects.map((e) => toDraft(e, catalog)) : [newDraftEffect("addPoints", catalog)],
  );
  const [limitPerMember, setLimitPerMember] = useState<number | null>(rule?.limitPerMember ?? null);
  const [error, setError] = useState<string | null>(null);

  const preview = ruleSentence(
    { conditions, effects: effects.map(fromDraft), limitPerMember },
    eventType,
    catalog,
  );

  const updateCondition = (index: number, next: DraftCondition) =>
    setConditions((list) => list.map((c, i) => (i === index ? next : c)));
  const updateEffect = (index: number, patch: Partial<DraftEffect>) =>
    setEffects((list) => list.map((e, i) => (i === index ? { ...e, ...patch } : e)));

  const save = () => {
    const problem = validate(name, conditions, effects);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    startTransition(async () => {
      const result = await saveEventRule(eventType.id, rule?.id ?? null, {
        name: name.trim(),
        isActive: rule?.isActive ?? true,
        conditions,
        effects: effects.map(fromDraft),
        limitPerMember,
      });
      if (!result.ok) {
        setError(result.error ?? "Couldn't save the rule.");
        return;
      }
      toast.success(result.message ?? "Rule saved.");
      revalidate.eventTypes();
      onDone();
    });
  };

  return (
    <div className="space-y-5">
      <Field label="Rule name" htmlFor="rule-name">
        <Input
          id="rule-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Big basket bonus"
          autoFocus
        />
      </Field>

      <Clause keyword="When">
        <div className="flex h-10 items-center gap-2 rounded-lg border border-dashed border-line px-3 text-sm text-foreground">
          <BoltIcon className="text-accent-violet" />
          <span className="font-medium">{eventType.name}</span>
          <span className="text-muted">happens</span>
        </div>
      </Clause>

      <Clause keyword="If" hint="All of these must be true">
        {conditions.length === 0 && (
          <p className="text-[0.8125rem] text-muted">
            No conditions, so the rule runs on every &ldquo;{eventType.name}&rdquo; event.
          </p>
        )}
        {conditions.map((condition, i) => (
          <ConditionRow
            key={i}
            condition={condition}
            fields={fields}
            eventName={eventType.name}
            onChange={(next) => updateCondition(i, next)}
            onRemove={() => setConditions((list) => list.filter((_, j) => j !== i))}
          />
        ))}
        <AddButton
          onClick={() =>
            setConditions((list) => {
              const fresh = conditionFor(fields[0]);
              return [...list, { ...fresh, value: valueToInput(fresh.value) }];
            })
          }
        >
          Add condition
        </AddButton>
      </Clause>

      <Clause keyword="Then" hint="All of these happen">
        {effects.map((effect, i) => (
          <EffectRow
            key={i}
            effect={effect}
            eventType={eventType}
            catalog={catalog}
            onChange={(patch) => updateEffect(i, patch)}
            onRemove={() => setEffects((list) => list.filter((_, j) => j !== i))}
          />
        ))}
        <AddButton onClick={() => setEffects((list) => [...list, newDraftEffect("addPoints", catalog)])}>
          Add effect
        </AddButton>
        {effects.some((e) => e.type === "addPoints") && (
          <p className="text-xs text-faint">
            The member&apos;s tier multiplier applies to earned points, the same as a manual earn.
          </p>
        )}
        {effects.some((e) => e.type === "burnPoints") && (
          <p className="text-xs text-faint">
            A burn is skipped when the member doesn&apos;t have enough points, the same as a manual burn.
          </p>
        )}
      </Clause>

      <Clause keyword="Limit">
        <div className="w-full sm:w-80">
          <Select
            aria-label="How often a member can trigger this rule"
            value={limitPerMember === 1 ? "once" : limitPerMember === null ? "always" : "custom"}
            onChange={(e) => setLimitPerMember(e.target.value === "once" ? 1 : null)}
          >
            <option value="always">Every time the event happens</option>
            <option value="once">Only the first time per member</option>
            {/* Set through the API only; kept so editing doesn't drop it. */}
            {limitPerMember !== null && limitPerMember > 1 && (
              <option value="custom">Up to {limitPerMember} times per member</option>
            )}
          </Select>
        </div>
      </Clause>

      <div className="flex items-start gap-2.5 rounded-lg bg-primary-subtle px-3.5 py-3 text-sm text-primary-subtle-fg">
        <SparklesIcon className="mt-0.5 shrink-0" />
        <p>
          <span className="font-semibold">In plain words: </span>
          {preview}
        </p>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="flex justify-end gap-2 pt-1">
        <Button variant="secondary" onClick={onDone} disabled={pending}>
          Cancel
        </Button>
        <Button onClick={save} loading={pending}>
          {rule ? "Save changes" : "Create rule"}
        </Button>
      </div>
    </div>
  );
}

function Clause({
  keyword,
  hint,
  children,
}: {
  keyword: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="grid gap-2 sm:grid-cols-[4.5rem_minmax(0,1fr)]">
      <div className="sm:pt-2">
        <span className="inline-flex rounded-md bg-surface-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-muted">
          {keyword}
        </span>
      </div>
      <div className="space-y-2">
        {hint && <p className="text-[0.8125rem] font-medium text-foreground sm:pt-2">{hint}</p>}
        {children}
      </div>
    </section>
  );
}

function FieldSelect({
  label,
  value,
  fields,
  eventName,
  onChange,
}: {
  label: string;
  value: string;
  fields: FieldDef[];
  /** Groups event attributes under this heading; omit when there are none. */
  eventName?: string;
  onChange: (field: FieldDef) => void;
}) {
  const eventFields = fields.filter((f) => f.group === "event");
  const memberFields = fields.filter((f) => f.group === "member");
  return (
    <Select
      aria-label={label}
      value={value}
      onChange={(e) => {
        const next = fields.find((f) => f.value === e.target.value);
        if (next) onChange(next);
      }}
    >
      {eventName && eventFields.length > 0 && (
        <optgroup label={`${eventName} event`}>
          {eventFields.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </optgroup>
      )}
      <optgroup label="Member">
        {memberFields.map((f) => (
          <option key={f.value} value={f.value}>
            {f.label}
          </option>
        ))}
      </optgroup>
    </Select>
  );
}

function ConditionRow({
  condition,
  fields,
  eventName,
  onChange,
  onRemove,
}: {
  condition: DraftCondition;
  fields: FieldDef[];
  eventName: string;
  onChange: (next: DraftCondition) => void;
  onRemove: () => void;
}) {
  const field = fields.find((f) => f.value === condition.field) ?? fields[0];

  return (
    <div className="grid gap-2 rounded-lg border border-line p-2 sm:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)_auto] sm:border-0 sm:p-0">
      <FieldSelect
        label="Field"
        value={condition.field}
        fields={fields}
        eventName={eventName}
        onChange={(next) => {
          const fresh = conditionFor(next);
          onChange({ ...fresh, value: valueToInput(fresh.value) });
        }}
      />
      <Select
        aria-label="Operator"
        value={condition.operator}
        onChange={(e) => onChange({ ...condition, operator: e.target.value as RuleOperator })}
      >
        {operatorsFor(field).map((op) => (
          <option key={op} value={op}>
            {operatorLabel(field, op)}
          </option>
        ))}
      </Select>
      <ValueInput field={field} value={condition.value} onChange={(value) => onChange({ ...condition, value })} />
      <RemoveButton label="Remove condition" onClick={onRemove} />
    </div>
  );
}

function ValueInput({
  field,
  value,
  onChange,
  allowEmpty = false,
}: {
  field: FieldDef;
  value: string;
  onChange: (value: string) => void;
  /** Offer an empty choice, meaning "clear the value". */
  allowEmpty?: boolean;
}) {
  if (field.options) {
    return (
      <Select aria-label="Value" value={value} onChange={(e) => onChange(e.target.value)}>
        {allowEmpty && <option value="">Empty</option>}
        {field.options.length === 0 && !allowEmpty && <option value="">Nothing to choose yet</option>}
        {field.options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </Select>
    );
  }
  return (
    <Input
      aria-label="Value"
      type={field.kind === "number" ? "number" : field.kind === "date" ? "date" : "text"}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={allowEmpty ? "Empty clears it" : "Value"}
    />
  );
}

function NamedSelect({
  label,
  value,
  items,
  empty,
  onChange,
}: {
  label: string;
  value: string;
  items: { id: string; name: string }[];
  empty: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="min-w-0 flex-1">
      <Select aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} disabled={!items.length}>
        {!items.length && <option value="">{empty}</option>}
        {items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
          </option>
        ))}
      </Select>
    </div>
  );
}

function EffectRow({
  effect,
  eventType,
  catalog,
  onChange,
  onRemove,
}: {
  effect: DraftEffect;
  eventType: EventType;
  catalog: Catalog;
  onChange: (patch: Partial<DraftEffect>) => void;
  onRemove: () => void;
}) {
  const writable = updatableFields(catalog);
  const setFields = (fields: DraftFieldUpdate[]) => onChange({ fields });

  return (
    <div className="grid gap-2 rounded-lg border border-line p-2 sm:grid-cols-[minmax(0,1.3fr)_minmax(0,2fr)_auto] sm:border-0 sm:p-0">
      <Select
        aria-label="Effect"
        value={effect.type}
        onChange={(e) => onChange({ type: e.target.value as RuleEffectType, fromAttribute: "" })}
      >
        {EFFECT_TYPES.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </Select>

      <div className="flex min-w-0 items-center gap-2">
        {(effect.type === "addPoints" || effect.type === "burnPoints") && (
          <AmountInput
            label="Points"
            value={effect.points}
            fromAttribute={effect.fromAttribute}
            attributes={eventType.attributes}
            onChange={onChange}
            valueKey="points"
          />
        )}
        {effect.type === "grantReward" && (
          <NamedSelect
            label="Reward"
            value={effect.rewardId}
            items={catalog.rewards}
            empty="No rewards yet"
            onChange={(rewardId) => onChange({ rewardId })}
          />
        )}
        {(effect.type === "addChallengeProgress" || effect.type === "assignChallenge") && (
          <NamedSelect
            label="Challenge"
            value={effect.challengeId}
            items={catalog.challenges}
            empty="No challenges yet"
            onChange={(challengeId) => onChange({ challengeId })}
          />
        )}
        {(effect.type === "addToSegment" || effect.type === "removeFromSegment") && (
          <NamedSelect
            label="Segment"
            value={effect.segmentId}
            items={catalog.segments}
            empty="No segments yet"
            onChange={(segmentId) => onChange({ segmentId })}
          />
        )}
        {effect.type === "updateMember" && (
          <p className="text-[0.8125rem] text-muted">Set these member fields:</p>
        )}
      </div>

      <RemoveButton label="Remove effect" onClick={onRemove} />

      {effect.type === "addChallengeProgress" && (
        <div className="flex min-w-0 items-center gap-2 sm:col-start-2">
          <span className="text-sm text-muted">by</span>
          <AmountInput
            label="Progress"
            value={effect.amount}
            fromAttribute={effect.fromAttribute}
            attributes={eventType.attributes}
            onChange={onChange}
            valueKey="amount"
          />
        </div>
      )}

      {effect.type === "updateMember" && (
        <div className="space-y-2 border-l-2 border-line pl-3 sm:col-span-3 sm:ml-1">
          {effect.fields.map((update, i) => (
            <FieldUpdateRow
              key={i}
              update={update}
              writable={writable}
              eventType={eventType}
              onChange={(next) => setFields(effect.fields.map((f, j) => (j === i ? next : f)))}
              onRemove={() => setFields(effect.fields.filter((_, j) => j !== i))}
            />
          ))}
          <AddButton onClick={() => setFields([...effect.fields, fieldUpdateFor(writable[0])])}>
            Add field
          </AddButton>
          <p className="text-xs text-faint">
            Name and phone belong to the person, so a change shows in every program.
          </p>
        </div>
      )}
    </div>
  );
}

/** A number an effect uses: fixed, or whatever the event sends for one of its
 *  number attributes. Without number attributes it's just the fixed amount. */
function AmountInput({
  label,
  value,
  fromAttribute,
  attributes,
  valueKey,
  onChange,
}: {
  label: string;
  value: string;
  fromAttribute: string;
  attributes: EventAttribute[];
  valueKey: "points" | "amount";
  onChange: (patch: Partial<DraftEffect>) => void;
}) {
  const numbers = attributes.filter((a) => a.type === "number");
  return (
    <>
      {numbers.length > 0 && (
        <div className="min-w-0 flex-1">
          <Select
            aria-label={`${label} source`}
            value={fromAttribute}
            onChange={(e) => onChange({ fromAttribute: e.target.value })}
          >
            <option value="">a fixed amount</option>
            {numbers.map((a) => (
              <option key={a.key} value={a.key}>
                the event&apos;s {a.label.toLowerCase()}
              </option>
            ))}
          </Select>
        </div>
      )}
      {!fromAttribute && (
        // The wrapper sets the width: Input's own w-full would win over a class on it.
        <div className="w-24 shrink-0">
          <Input
            aria-label={label}
            type="number"
            min={1}
            value={value}
            onChange={(e) => onChange({ [valueKey]: e.target.value })}
          />
        </div>
      )}
    </>
  );
}

function FieldUpdateRow({
  update,
  writable,
  eventType,
  onChange,
  onRemove,
}: {
  update: DraftFieldUpdate;
  writable: FieldDef[];
  eventType: EventType;
  onChange: (next: DraftFieldUpdate) => void;
  onRemove: () => void;
}) {
  const field = writable.find((f) => f.value === update.field) ?? writable[0];
  const sources = copyableAttributes(eventType, field);

  return (
    <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto]">
      <FieldSelect
        label="Member field"
        value={update.field}
        fields={writable}
        onChange={(next) => onChange(fieldUpdateFor(next))}
      />
      <Select
        aria-label="Set it to"
        value={update.fromAttribute}
        onChange={(e) => onChange({ ...update, fromAttribute: e.target.value })}
      >
        <option value="">to a fixed value</option>
        {sources.map((a) => (
          <option key={a.key} value={a.key}>
            to the event&apos;s {a.label.toLowerCase()}
          </option>
        ))}
      </Select>
      {update.fromAttribute ? (
        <div className="hidden sm:block" />
      ) : (
        <ValueInput
          field={field}
          value={update.value}
          allowEmpty={update.field !== "member.name"}
          onChange={(value) => onChange({ ...update, value })}
        />
      )}
      <RemoveButton label="Remove field" onClick={onRemove} />
    </div>
  );
}

function AddButton({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <Button variant="ghost" size="sm" className="-ml-2" onClick={onClick}>
      <PlusIcon /> {children}
    </Button>
  );
}

function RemoveButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <Button variant="ghost" size="icon" aria-label={label} onClick={onClick} className="justify-self-end">
      <XIcon />
    </Button>
  );
}
