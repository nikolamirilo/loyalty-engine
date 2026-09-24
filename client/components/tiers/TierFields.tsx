"use client";

import { useState } from "react";

import { conditionFor, operatorLabel, operatorsFor, valueToInput, type FieldDef } from "@/lib/conditions";
import { tierConditionFields, type TierCatalog } from "@/lib/tiers/conditions";
import { useMemberAttributes, useSegments } from "@/lib/swr/hooks";
import type { RuleCondition, RuleOperator, Tier } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Field, Input, Select } from "@/components/ui/Field";
import { PlusIcon, XIcon } from "@/components/ui/icons";

/** Shared form fields for creating and editing a tier: name, rank, multiplier,
 *  and the conditions a member must all meet to qualify. Conditions are held
 *  as local state and serialized into a hidden input for the surrounding
 *  `FormDialog`'s server action to parse - the same tradeoff `RuleEditorDialog`
 *  makes, just without that dialog's own open/close/save plumbing, since a
 *  tier has no effects or preview sentence to justify it. */
export function TierFields({ tier }: { tier?: Tier }) {
  const { data: segments } = useSegments();
  const { data: memberAttributes } = useMemberAttributes();
  const catalog: TierCatalog = { segments: segments ?? [], memberAttributes: memberAttributes ?? [] };
  const fields = tierConditionFields(catalog);

  const [conditions, setConditions] = useState<RuleCondition[]>(
    () => tier?.conditions.map((c) => ({ ...c, value: valueToInput(c.value) })) ?? [],
  );

  const updateCondition = (index: number, next: RuleCondition) =>
    setConditions((list) => list.map((c, i) => (i === index ? next : c)));

  return (
    <>
      <Field label="Name" htmlFor="tier-name">
        <Input
          id="tier-name"
          name="name"
          placeholder="e.g. Gold"
          defaultValue={tier?.name}
          required
        />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Rank" htmlFor="tier-rank" hint="highest tried first">
          <Input
            id="tier-rank"
            name="rank"
            type="number"
            step={1}
            defaultValue={tier?.rank ?? 0}
            required
          />
        </Field>
        <Field label="Multiplier" htmlFor="tier-mult" hint="> 0">
          <Input
            id="tier-mult"
            name="multiplier"
            type="number"
            min={0}
            step="0.1"
            defaultValue={tier?.multiplier ?? 1}
            required
          />
        </Field>
      </div>

      <Field
        label="Conditions"
        help="All must match. No conditions means every member qualifies - useful for a catch-all lowest tier."
      >
        <div className="space-y-2">
          {conditions.length === 0 && (
            <p className="text-[0.8125rem] text-muted">Every member qualifies.</p>
          )}
          {conditions.map((condition, i) => (
            <TierConditionRow
              key={i}
              condition={condition}
              fields={fields}
              onChange={(next) => updateCondition(i, next)}
              onRemove={() => setConditions((list) => list.filter((_, j) => j !== i))}
            />
          ))}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="-ml-2"
            onClick={() =>
              setConditions((list) => {
                const fresh = conditionFor(fields[0]);
                return [...list, { ...fresh, value: valueToInput(fresh.value) }];
              })
            }
          >
            <PlusIcon /> Add condition
          </Button>
        </div>
      </Field>

      <input type="hidden" name="conditions" value={JSON.stringify(conditions)} />
    </>
  );
}

function TierConditionRow({
  condition,
  fields,
  onChange,
  onRemove,
}: {
  condition: RuleCondition;
  fields: FieldDef[];
  onChange: (next: RuleCondition) => void;
  onRemove: () => void;
}) {
  const field = fields.find((f) => f.value === condition.field) ?? fields[0];

  return (
    <div className="grid gap-2 rounded-lg border border-line p-2 sm:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)_auto] sm:border-0 sm:p-0">
      <Select
        aria-label="Field"
        value={condition.field}
        onChange={(e) => {
          const next = fields.find((f) => f.value === e.target.value);
          if (!next) return;
          const fresh = conditionFor(next);
          onChange({ ...fresh, value: valueToInput(fresh.value) });
        }}
      >
        {fields.map((f) => (
          <option key={f.value} value={f.value}>
            {f.label}
          </option>
        ))}
      </Select>
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
      <ValueInput field={field} value={valueToInput(condition.value)} onChange={(value) => onChange({ ...condition, value })} />
      <Button variant="ghost" size="icon" aria-label="Remove condition" onClick={onRemove}>
        <XIcon />
      </Button>
    </div>
  );
}

function ValueInput({
  field,
  value,
  onChange,
}: {
  field: FieldDef;
  value: string;
  onChange: (value: string) => void;
}) {
  if (field.options) {
    return (
      <Select aria-label="Value" value={value} onChange={(e) => onChange(e.target.value)}>
        {field.options.length === 0 && <option value="">Nothing to choose yet</option>}
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
      placeholder="Value"
    />
  );
}
