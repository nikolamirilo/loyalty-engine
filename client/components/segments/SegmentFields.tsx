"use client";

import { useState } from "react";

import type { Segment } from "@/lib/types";
import { Field, Input, Textarea } from "@/components/ui/Field";

const DEFAULT_SWATCH = "#94a3b8";
const HEX_RE = /^#[0-9a-f]{6}$/i;

/** Shared form fields for creating and editing a segment. */
export function SegmentFields({ segment }: { segment?: Segment }) {
  const [color, setColor] = useState(segment?.color ?? "");

  return (
    <>
      <Field label="Name" htmlFor="segment-name">
        <Input
          id="segment-name"
          name="name"
          placeholder="e.g. VIP"
          defaultValue={segment?.name}
          required
        />
      </Field>
      <Field label="Description" htmlFor="segment-desc" hint="optional">
        <Textarea
          id="segment-desc"
          name="description"
          placeholder="What this segment represents"
          defaultValue={segment?.description ?? ""}
        />
      </Field>
      <Field
        label="Color"
        htmlFor="segment-color"
        hint="optional"
        help="Accent used for this segment's badge - pick a color or type a hex value"
      >
        <div className="flex items-center gap-2">
          <input
            type="color"
            aria-label="Pick a color"
            value={HEX_RE.test(color) ? color : DEFAULT_SWATCH}
            onChange={(e) => setColor(e.target.value)}
            className="h-9 w-9 shrink-0 cursor-pointer rounded-lg border border-line bg-surface p-1"
          />
          <Input
            id="segment-color"
            name="color"
            placeholder="#f59e0b"
            value={color}
            onChange={(e) => setColor(e.target.value)}
          />
        </div>
      </Field>
    </>
  );
}
