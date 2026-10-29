import { describe, expect, it } from "vitest";

import { programThemeCss, STOCK_PRIMARY } from "./theme";

const DARK_QUERY = "@media (prefers-color-scheme: dark){html:root{";

/** The custom properties set for each colour scheme. */
function tokens(css: string): { light: Record<string, string>; dark: Record<string, string> } {
  const block = (from: number) => {
    const body = css.slice(from, css.indexOf("}", from));
    return Object.fromEntries(body.split(";").map((declaration) => declaration.split(":")));
  };
  return {
    light: block("html:root{".length),
    dark: block(css.indexOf(DARK_QUERY) + DARK_QUERY.length),
  };
}

// WCAG relative luminance and contrast, written out independently of theme.ts.
function luminance(hex: string): number {
  const n = Number.parseInt(hex.slice(1), 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// The dark theme's surface, from app/globals.css.
const DARK_SURFACE = "#131a2c";

describe("programThemeCss", () => {
  it("returns null when the program sets no colour", () => {
    expect(programThemeCss(null)).toBeNull();
    expect(programThemeCss(undefined)).toBeNull();
    expect(programThemeCss({ primaryColor: null, secondaryColor: null })).toBeNull();
  });

  // The value is written straight into a <style> element.
  it.each(["red", "#fff", "#12345g", "#5b4bd6;}body{display:none", "red;}body{display:none}"])(
    "rejects %s, which is not a six-digit hex colour",
    (value) => {
      expect(programThemeCss({ primaryColor: value, secondaryColor: null })).toBeNull();
      expect(programThemeCss({ primaryColor: null, secondaryColor: value })).toBeNull();
    },
  );

  it("drops an invalid colour and keeps a valid one", () => {
    const css = programThemeCss({
      primaryColor: STOCK_PRIMARY,
      secondaryColor: "#000000;}body{display:none",
    })!;
    expect(css).not.toContain("body");
    expect(css).not.toContain("--secondary");
    expect(tokens(css).light["--primary"]).toBe(STOCK_PRIMARY);
  });

  it("writes both colour schemes", () => {
    const css = programThemeCss({ primaryColor: STOCK_PRIMARY, secondaryColor: null })!;
    expect(css.startsWith("html:root{")).toBe(true);
    expect(css).toContain(DARK_QUERY);
    const { light, dark } = tokens(css);
    for (const name of ["--primary", "--primary-hover", "--primary-fg", "--primary-subtle", "--primary-subtle-fg", "--ring"]) {
      expect(light[name]).toMatch(/^#[0-9a-f]{6}$/);
      expect(dark[name]).toMatch(/^#[0-9a-f]{6}$/);
    }
  });

  it("keeps the brand colour itself as the light primary", () => {
    const css = programThemeCss({ primaryColor: "#1E3A8A", secondaryColor: null })!;
    expect(tokens(css).light["--primary"]).toBe("#1e3a8a");
  });

  it("lowercases the secondary colour in both schemes", () => {
    const css = programThemeCss({ primaryColor: null, secondaryColor: "#AABBCC" })!;
    const { light, dark } = tokens(css);
    expect(light["--secondary"]).toBe("#aabbcc");
    expect(dark["--secondary"]).toBe("#aabbcc");
    expect(light["--primary"]).toBeUndefined();
  });

  // A spread of brand colours: the stock purple, a dark navy, a bright yellow,
  // white, black and a saturated green.
  it.each([STOCK_PRIMARY, "#1e3a8a", "#facc15", "#ffffff", "#000000", "#16a34a"])(
    "keeps %s readable",
    (brand) => {
      const { light, dark } = tokens(programThemeCss({ primaryColor: brand, secondaryColor: null })!);
      for (const scheme of [light, dark]) {
        expect(contrast(scheme["--primary-fg"], scheme["--primary"])).toBeGreaterThanOrEqual(4.5);
        expect(contrast(scheme["--primary-subtle-fg"], scheme["--primary-subtle"])).toBeGreaterThanOrEqual(4.5);
      }
      // Dark theme primary doubles as link text on the dark surface.
      expect(contrast(dark["--primary"], DARK_SURFACE)).toBeGreaterThanOrEqual(4.5);
    },
  );
});
