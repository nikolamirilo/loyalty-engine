import { describe, expect, it } from "vitest";

import { previewKey } from "./custom-attributes";

// Each expected key is what slugify() in api/app/services/custom_attributes.py
// returns for the label, so a drift between the preview and the server shows
// up here. Labels the server rejects (no leading letter) are left out: the
// preview has nothing to match for those.
describe("previewKey matches the API's slugify", () => {
  it.each([
    ["Favourite colour!", "favouriteColour"],
    ["favorite color", "favoriteColor"],
    ["  Shoe   size (EU) ", "shoeSizeEu"],
    ["VIP-level", "vipLevel"],
    ["ALL CAPS LABEL", "allCapsLabel"],
    ["camelCase input", "camelcaseInput"],
    ["x_y_z", "xYZ"],
    ["Größe in cm", "grEInCm"],
    ["café au lait", "cafAuLait"],
    ["Ünïcödé only", "nCDOnly"],
    ["a".repeat(70), "a".repeat(63)],
    ["word ".repeat(20), "wordWordWordWordWordWordWordWordWordWordWordWordWordWordWordWor"],
  ])("%j -> %s", (label, key) => {
    expect(previewKey(label)).toBe(key);
  });
});
