import "server-only";

/**
 * Upstream Loyalty Engine API configuration — SERVER ONLY.
 *
 * The bearer token must never reach the browser, so this module is guarded with
 * `server-only` (importing it from a Client Component becomes a build error).
 * Shared by the API proxy route handler (browser/SWR calls) and by lib/api.ts
 * (Server Actions) so both agree on the same upstream base URL and token.
 */

/**
 * Read an env var, treating blank as unset. `??` alone is not enough: a bare
 * `API_BASE_URL=` in a .env file yields "", which is not nullish, so the
 * default would be skipped and every request would build an invalid URL.
 */
function env(name: string): string | undefined {
  const raw = process.env[name]?.trim();
  return raw ? raw : undefined;
}

export const UPSTREAM_BASE_URL = (
  env("API_BASE_URL") ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export const UPSTREAM_TOKEN = env("API_TOKEN") ?? "";
