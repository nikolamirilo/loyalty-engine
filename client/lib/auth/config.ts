/**
 * Admin-gate configuration.
 *
 * Reads the admin credentials and the session-signing secret from the
 * environment and fails fast if any are missing, mirroring how the API's
 * `API_TOKEN` is handled. Only import this from server-side modules (Server
 * Actions, Server Components, the proxy) - it must never reach the browser.
 */

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `${name} is not set. Add it to the environment or a .env file.`,
    );
  }
  return value;
}

export const ADMIN_USERNAME = required("ADMIN_USERNAME");
export const ADMIN_PASSWORD = required("ADMIN_PASSWORD");
export const AUTH_SECRET = required("AUTH_SECRET");

/** Name of the signed session cookie set on successful login. */
export const SESSION_COOKIE = "admin_session";

/** How long a successful login stays valid (7 days). */
export const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000;

/** Failed logins allowed from one IP before the lockout kicks in. */
export const MAX_ATTEMPTS = 3;

/** How long the lockout lasts once triggered (10 minutes). */
export const LOCKOUT_MS = 10 * 60 * 1000;
