import { createHmac } from "node:crypto";

import { describe, expect, it } from "vitest";

import { createToken, verifyToken } from "@/lib/auth/token";

import { createMemberToken, verifyMemberToken } from "./token";

const HOUR = 60 * 60 * 1000;
const MEMBER = "6f1c2a9e-0b7d-4e5a-9c3f-2d8b1e4a7c60";
const PROGRAM = "0d3e5f7a-1b2c-4d6e-8f9a-b0c1d2e3f405";
const OTHER = "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d";

/** Signs the way token.ts does, to build tokens it would never create itself. */
function sign(payload: string): string {
  return createHmac("sha256", process.env.AUTH_SECRET!).update(payload).digest("hex");
}

describe("member session token", () => {
  it("round-trips the member and the program", () => {
    const token = createMemberToken(MEMBER, PROGRAM, Date.now() + HOUR);
    expect(verifyMemberToken(token)).toEqual({ memberId: MEMBER, programId: PROGRAM });
  });

  it("rejects an expired token", () => {
    expect(verifyMemberToken(createMemberToken(MEMBER, PROGRAM, Date.now() - 1))).toBeNull();
  });

  it("rejects the old two-part token, which carried no program", () => {
    const payload = `${MEMBER}.${Date.now() + HOUR}`;
    expect(verifyMemberToken(`${payload}.${sign(payload)}`)).toBeNull();
  });

  it("rejects a token whose member was swapped", () => {
    const token = createMemberToken(MEMBER, PROGRAM, Date.now() + HOUR);
    expect(verifyMemberToken(token.replace(MEMBER, OTHER))).toBeNull();
  });

  it("rejects a token whose program was swapped", () => {
    const token = createMemberToken(MEMBER, PROGRAM, Date.now() + HOUR);
    expect(verifyMemberToken(token.replace(PROGRAM, OTHER))).toBeNull();
  });

  it("rejects malformed and missing tokens", () => {
    expect(verifyMemberToken("")).toBeNull();
    expect(verifyMemberToken(null)).toBeNull();
    expect(verifyMemberToken(undefined)).toBeNull();
    expect(verifyMemberToken(`${MEMBER}.${PROGRAM}.${Date.now() + HOUR}.`)).toBeNull();
  });

  // Both formats are signed with AUTH_SECRET, so only their shape keeps a
  // member from presenting their cookie as an admin session, or the reverse.
  it("never accepts an admin token, and the admin check never accepts it", () => {
    const expiresAt = Date.now() + HOUR;
    expect(verifyToken(createMemberToken(MEMBER, PROGRAM, expiresAt))).toBe(false);
    expect(verifyMemberToken(createToken(expiresAt))).toBeNull();
  });
});
