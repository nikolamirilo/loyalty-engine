import { afterEach, describe, expect, it, vi } from "vitest";

import { createToken, verifyToken } from "./token";

const HOUR = 60 * 60 * 1000;

describe("admin session token", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("accepts a token it signed that has not expired", () => {
    expect(verifyToken(createToken(Date.now() + HOUR))).toBe(true);
  });

  it("rejects an expired token", () => {
    expect(verifyToken(createToken(Date.now() - 1))).toBe(false);
  });

  it("stops accepting a token the moment it expires", () => {
    vi.useFakeTimers();
    const token = createToken(Date.now() + HOUR);
    vi.advanceTimersByTime(HOUR - 1);
    expect(verifyToken(token)).toBe(true);
    vi.advanceTimersByTime(1);
    expect(verifyToken(token)).toBe(false);
  });

  it("rejects a tampered signature", () => {
    const token = createToken(Date.now() + HOUR);
    const flipped = token.endsWith("0") ? "1" : "0";
    expect(verifyToken(token.slice(0, -1) + flipped)).toBe(false);
  });

  it("rejects an expiry pushed out under the original signature", () => {
    const expiresAt = Date.now() + HOUR;
    const signature = createToken(expiresAt).split(".")[1];
    expect(verifyToken(`${expiresAt + 30 * 24 * HOUR}.${signature}`)).toBe(false);
  });

  it.each([
    ["no dot", "1234567890"],
    ["empty", ""],
    ["nothing before the dot", ".abcdef"],
    ["empty signature", `${Date.now() + HOUR}.`],
    ["non-hex signature", `${Date.now() + HOUR}.${"z".repeat(64)}`],
    ["non-numeric expiry", `soon.${"a".repeat(64)}`],
  ])("rejects a malformed token: %s", (_label, token) => {
    expect(verifyToken(token)).toBe(false);
  });

  it("rejects a missing token", () => {
    expect(verifyToken(null)).toBe(false);
    expect(verifyToken(undefined)).toBe(false);
  });
});
