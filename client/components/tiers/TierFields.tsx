"use client";

import type { Tier } from "@/lib/types";
import { Field, Input } from "@/components/ui/Field";

/** Shared form fields for creating and editing a tier. */
export function TierFields({ tier }: { tier?: Tier }) {
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
        <Field label="Min points" htmlFor="tier-min" hint="≥ 0">
          <Input
            id="tier-min"
            name="minPoints"
            type="number"
            min={0}
            step={1}
            defaultValue={tier?.minPoints ?? 0}
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
    </>
  );
}
