import "server-only";

/**
 * Upstream Loyalty Engine API configuration — SERVER ONLY.
 *
 * The bearer token must never reach the browser, so this module is guarded with
 * `server-only` (importing it from a Client Component becomes a build error).
 * Shared by the API proxy route handler (browser/SWR calls) and by lib/api.ts
 * (Server Actions) so both agree on the same upstream base URL and token.
 */

export const UPSTREAM_BASE_URL = (
  process.env.API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export const UPSTREAM_TOKEN = process.env.API_TOKEN ?? "";
