import { describe, expect, it } from "vitest";

import {
  cn,
  compactNumber,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPrice,
  humanize,
  initials,
  signedNumber,
  toDatetimeLocalValue,
} from "./format";

// vitest.config.ts runs the tests with TZ=UTC, so local time is UTC here.

describe("dates from the API", () => {
  it("treats a timestamp without a zone as UTC", () => {
    expect(formatDateTime("2026-03-01T14:05:00")).toBe(formatDateTime("2026-03-01T14:05:00Z"));
    expect(toDatetimeLocalValue("2026-03-01T14:05:00")).toBe("2026-03-01T14:05");
  });

  it("respects a zone when there is one", () => {
    expect(toDatetimeLocalValue("2026-03-01T14:05:00+02:00")).toBe("2026-03-01T12:05");
    expect(toDatetimeLocalValue("2026-03-01T14:05:00.123456Z")).toBe("2026-03-01T14:05");
  });

  it("formats a date", () => {
    expect(formatDate("2026-03-01T23:30:00")).toBe("Mar 1, 2026");
  });

  it("shows a dash for a missing or unreadable date", () => {
    expect(formatDate(null)).toBe("-");
    expect(formatDate("not a date")).toBe("-");
    expect(formatDateTime(undefined)).toBe("-");
    expect(toDatetimeLocalValue("")).toBe("");
  });
});

describe("numbers", () => {
  it("formats prices from minor units", () => {
    expect(formatPrice(1450, "EUR")).toBe("€14.50");
    expect(formatPrice(0, "USD")).toBe("$0.00");
  });

  it("switches to compact notation at 10K", () => {
    expect(compactNumber(9_999)).toBe("9,999");
    expect(compactNumber(10_000)).toBe("10K");
    expect(compactNumber(12_900)).toBe("12.9K");
    expect(compactNumber(4_200_000)).toBe("4.2M");
    expect(compactNumber(-12_900)).toBe("-12.9K");
  });

  it("signs points", () => {
    expect(signedNumber(100)).toBe("+100");
    expect(signedNumber(-30)).toBe("-30");
    expect(signedNumber(0)).toBe("0");
    expect(signedNumber(1284)).toBe("+1,284");
  });

  it("groups thousands", () => {
    expect(formatNumber(1284)).toBe("1,284");
  });
});

describe("text", () => {
  it("takes initials from the first and last name", () => {
    expect(initials("Ada Lovelace")).toBe("AL");
    expect(initials("Jean Claude Van Damme")).toBe("JD");
    expect(initials("  ada  ")).toBe("AD");
    expect(initials("   ")).toBe("?");
  });

  it("humanizes identifiers", () => {
    expect(humanize("in_progress")).toBe("In progress");
    expect(humanize("double-opt-in")).toBe("Double opt in");
    expect(humanize("__pending__")).toBe("Pending");
  });

  it("joins only truthy class names", () => {
    expect(cn("a", false, null, undefined, "", "b")).toBe("a b");
  });
});
