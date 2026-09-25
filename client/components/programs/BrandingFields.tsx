"use client";

import { useEffect, useRef, useState } from "react";

import { HEX_COLOR, STOCK_PRIMARY } from "@/lib/theme";
import type { Program } from "@/lib/types";
import { BrandLogo } from "@/components/branding/BrandLogo";
import { Button } from "@/components/ui/Button";
import { Field, Input, Label } from "@/components/ui/Field";

const LOGO_TYPES = "image/png,image/jpeg,image/webp,image/svg+xml";
const STOCK_SECONDARY = "#eb6834";

/**
 * Logo and brand colours for the program dialogs. Everything here is optional:
 * left alone, a program keeps the stock look.
 *
 * The fields submit as `logo` (a file, only when one was picked), `removeLogo`
 * and `primaryColor` / `secondaryColor` (hex, blank for the stock colour).
 * lib/programs/actions.ts reads them.
 */
export function BrandingFields({ program }: { program?: Program }) {
  return (
    <fieldset className="space-y-4 border-t border-line pt-4">
      <legend className="sr-only">Branding</legend>
      <p className="text-xs text-faint">
        Branding is optional. The console and the member app use this program&apos;s logo
        and colours when it is selected.
      </p>
      <LogoField current={program?.logoUrl ?? null} />
      <div className="grid gap-4 sm:grid-cols-2">
        <ColorField
          name="primaryColor"
          label="Primary colour"
          help="Buttons, links and highlights. Pick one that reads on white."
          stock={STOCK_PRIMARY}
          defaultValue={program?.primaryColor}
        />
        <ColorField
          name="secondaryColor"
          label="Secondary colour"
          help="Accent on the member tier card."
          stock={STOCK_SECONDARY}
          defaultValue={program?.secondaryColor}
        />
      </div>
    </fieldset>
  );
}

function LogoField({ current }: { current: string | null }) {
  const inputRef = useRef<HTMLInputElement>(null);
  // An object URL for the file just picked, released when replaced or unmounted.
  const [picked, setPicked] = useState<string | null>(null);
  // Only ever true when the program already has a logo to remove.
  const [removed, setRemoved] = useState(false);

  useEffect(() => {
    if (!picked) return;
    return () => URL.revokeObjectURL(picked);
  }, [picked]);

  const preview = picked ?? (removed ? null : current);

  const onPick = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setPicked(file ? URL.createObjectURL(file) : null);
    if (file) setRemoved(false);
  };

  const onRemove = () => {
    if (inputRef.current) inputRef.current.value = "";
    setPicked(null);
    setRemoved(current !== null);
  };

  return (
    <Field label="Logo" help="PNG, JPG, WebP or SVG, up to 2 MB.">
      <div className="flex items-center gap-3">
        {/* White like the logo will usually sit on; without one it previews
            the stock logo, which is what will show. */}
        <span className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-line bg-white p-1.5">
          <BrandLogo
            src={preview}
            alt={preview ? "Logo preview" : "Stock logo"}
            className={preview ? "max-h-full max-w-full" : "h-8 opacity-40"}
          />
        </span>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => inputRef.current?.click()}
          >
            {preview ? "Replace" : "Upload logo"}
          </Button>
          {preview && (
            <Button type="button" variant="ghost" size="sm" onClick={onRemove}>
              Remove
            </Button>
          )}
        </div>
      </div>
      {/* Hidden, not removed: a display:none file input still submits. */}
      <input
        ref={inputRef}
        type="file"
        name="logo"
        accept={LOGO_TYPES}
        onChange={onPick}
        className="hidden"
        aria-label="Logo file"
      />
      {removed && <input type="hidden" name="removeLogo" value="on" />}
    </Field>
  );
}

function ColorField({
  name,
  label,
  help,
  stock,
  defaultValue,
}: {
  name: string;
  label: string;
  help: string;
  stock: string;
  defaultValue?: string | null;
}) {
  // The text box is the field that submits; the swatch is a picker for it.
  // Blank means "stock colour", which is why it is not a bare <input
  // type="color"> - that can never be empty.
  const [value, setValue] = useState(defaultValue ?? "");
  const id = `program-${name}`;
  const valid = HEX_COLOR.test(value);

  return (
    <div>
      <Label htmlFor={id}>{label}</Label>
      <div className="flex items-center gap-2">
        <input
          type="color"
          value={valid ? value.toLowerCase() : stock}
          onChange={(e) => setValue(e.target.value)}
          aria-label={`Pick ${label.toLowerCase()}`}
          className="h-9 w-10 shrink-0 cursor-pointer rounded-lg border border-line bg-surface p-1"
        />
        <Input
          id={id}
          name={name}
          value={value}
          onChange={(e) => setValue(e.target.value.trim())}
          placeholder="Default"
          maxLength={7}
          spellCheck={false}
          autoComplete="off"
          className="font-mono"
        />
        {value && (
          <Button type="button" variant="ghost" size="sm" onClick={() => setValue("")}>
            Reset
          </Button>
        )}
      </div>
      <p className="mt-1 text-xs text-faint">{help}</p>
    </div>
  );
}
