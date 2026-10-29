import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearAttempts, lockRemainingMs, registerFailure } from "./attempts";
import { LOCKOUT_MS, MAX_ATTEMPTS } from "./config";

// The store lives on globalThis and outlasts each test, so every test gets an
// address of its own instead of resetting shared state.
let counter = 0;
const freshIp = () => `203.0.113.${++counter}`;

function failTimes(ip: string, times: number) {
  let last = registerFailure(ip);
  for (let i = 1; i < times; i++) last = registerFailure(ip);
  return last;
}

describe("admin login attempts", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("counts down the attempts left before locking", () => {
    const ip = freshIp();
    expect(MAX_ATTEMPTS).toBe(3);
    expect(registerFailure(ip)).toEqual({ locked: false, remainingMs: 0, attemptsLeft: 2 });
    expect(registerFailure(ip)).toEqual({ locked: false, remainingMs: 0, attemptsLeft: 1 });
    expect(lockRemainingMs(ip)).toBe(0);
  });

  it("locks for LOCKOUT_MS on the third failure", () => {
    const ip = freshIp();
    expect(failTimes(ip, 3)).toEqual({ locked: true, remainingMs: LOCKOUT_MS, attemptsLeft: 0 });
    expect(lockRemainingMs(ip)).toBe(LOCKOUT_MS);
    vi.advanceTimersByTime(60_000);
    expect(lockRemainingMs(ip)).toBe(LOCKOUT_MS - 60_000);
  });

  it("gives a fresh set of attempts once the lockout ends", () => {
    const ip = freshIp();
    failTimes(ip, 3);
    vi.advanceTimersByTime(LOCKOUT_MS);
    expect(lockRemainingMs(ip)).toBe(0);
    expect(registerFailure(ip)).toEqual({ locked: false, remainingMs: 0, attemptsLeft: 2 });
  });

  it("forgets earlier failures after a successful login", () => {
    const ip = freshIp();
    failTimes(ip, 2);
    clearAttempts(ip);
    expect(registerFailure(ip).attemptsLeft).toBe(2);
  });

  it("lifts a lockout when cleared", () => {
    const ip = freshIp();
    failTimes(ip, 3);
    clearAttempts(ip);
    expect(lockRemainingMs(ip)).toBe(0);
  });

  it("keeps each address's count separate", () => {
    const ip = freshIp();
    failTimes(ip, 3);
    const other = freshIp();
    expect(lockRemainingMs(other)).toBe(0);
    expect(registerFailure(other).attemptsLeft).toBe(2);
  });
});
