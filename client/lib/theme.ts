/**
 * Program branding -> CSS custom properties.
 *
 * Every coloured thing in the UI reads the `--primary*` tokens in
 * app/globals.css, so a program is themed by overriding just those. An admin
 * picks one brand colour; the hover, tint, text-on-tint and dark-mode shades
 * are derived here, and nudged until they meet WCAG AA contrast, so any brand
 * colour stays readable - a dark navy still shows up on the dark theme, a
 * bright yellow still gets dark text on its buttons.
 *
 * Pure functions with no React or Next imports, so the maths is easy to test
 * and the same output is produced wherever it runs.
 */

import type { Program } from "@/lib/types";

type Rgb = readonly [number, number, number];

export const HEX_COLOR = /^#[0-9a-f]{6}$/i;

/** The stock primary, shown in the colour picker while none is chosen. */
export const STOCK_PRIMARY = "#5b4bd6";

const WHITE: Rgb = [255, 255, 255];
const BLACK: Rgb = [0, 0, 0];

// The surfaces the tokens are read against - mirrors app/globals.css.
const LIGHT = { surface: [255, 255, 255] as Rgb, ink: [15, 23, 42] as Rgb };
const DARK = { surface: [19, 26, 44] as Rgb, ink: [11, 16, 32] as Rgb };

/** WCAG AA for body text. */
const MIN_CONTRAST = 4.5;

function parse(hex: string): Rgb {
  const n = Number.parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function toHex(rgb: Rgb): string {
  return `#${rgb.map((c) => Math.round(c).toString(16).padStart(2, "0")).join("")}`;
}

/** `weight` of `a`, the rest of `b`. */
function mix(a: Rgb, b: Rgb, weight: number): Rgb {
  return [0, 1, 2].map((i) => a[i] * weight + b[i] * (1 - weight)) as unknown as Rgb;
}

function luminance(rgb: Rgb): number {
  const [r, g, b] = rgb.map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: Rgb, b: Rgb): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/** `color` moved towards `towards` in small steps until it reads on `background`. */
function readableOn(color: Rgb, background: Rgb, towards: Rgb): Rgb {
  for (let weight = 1; weight > 0; weight -= 0.05) {
    const candidate = mix(color, towards, weight);
    if (contrast(candidate, background) >= MIN_CONTRAST) return candidate;
  }
  return towards;
}

/** Whichever of the two inks is easier to read on `background`. */
function inkOn(background: Rgb, light: Rgb, dark: Rgb): Rgb {
  return contrast(light, background) >= contrast(dark, background) ? light : dark;
}

function primaryTokens(brand: Rgb, scheme: "light" | "dark"): Record<string, string> {
  if (scheme === "light") {
    // The brand colour itself, untouched: it is what the customer will look for.
    const subtle = mix(brand, WHITE, 0.12);
    return {
      "--primary": toHex(brand),
      "--primary-hover": toHex(mix(brand, BLACK, 0.85)),
      "--primary-fg": toHex(inkOn(brand, WHITE, LIGHT.ink)),
      "--primary-subtle": toHex(subtle),
      "--primary-subtle-fg": toHex(readableOn(brand, subtle, BLACK)),
      "--ring": toHex(brand),
    };
  }
  // Dark theme: primary doubles as text colour (links, active tabs), so lift
  // it until it reads on the dark surface, as the stock dark palette does.
  const primary = readableOn(brand, DARK.surface, WHITE);
  const subtle = mix(brand, DARK.surface, 0.25);
  return {
    "--primary": toHex(primary),
    "--primary-hover": toHex(mix(primary, WHITE, 0.85)),
    "--primary-fg": toHex(inkOn(primary, WHITE, DARK.ink)),
    "--primary-subtle": toHex(subtle),
    "--primary-subtle-fg": toHex(readableOn(primary, subtle, WHITE)),
    "--ring": toHex(primary),
  };
}

function declarations(tokens: Record<string, string>): string {
  return Object.entries(tokens)
    .map(([name, value]) => `${name}:${value}`)
    .join(";");
}

/**
 * The stylesheet that applies a program's colours, or null when it has none.
 *
 * `html:root` outranks the plain `:root` in globals.css regardless of which
 * stylesheet loads last, and both colour schemes are written out because the
 * stock dark palette sits behind a media query of its own.
 */
export function programThemeCss(
  program: Pick<Program, "primaryColor" | "secondaryColor"> | null | undefined,
): string | null {
  const primary = program?.primaryColor;
  const secondary = program?.secondaryColor;
  // Re-checked here, not just trusted from the API: the value is written
  // straight into a <style> element.
  const hasPrimary = !!primary && HEX_COLOR.test(primary);
  const hasSecondary = !!secondary && HEX_COLOR.test(secondary);
  if (!hasPrimary && !hasSecondary) return null;

  const light: Record<string, string> = {};
  const dark: Record<string, string> = {};
  if (hasPrimary) {
    Object.assign(light, primaryTokens(parse(primary), "light"));
    Object.assign(dark, primaryTokens(parse(primary), "dark"));
  }
  if (hasSecondary) {
    light["--secondary"] = secondary.toLowerCase();
    dark["--secondary"] = secondary.toLowerCase();
  }
  return (
    `html:root{${declarations(light)}}` +
    `@media (prefers-color-scheme: dark){html:root{${declarations(dark)}}}`
  );
}
