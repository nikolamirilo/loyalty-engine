import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth/config";
import { verifyToken } from "@/lib/auth/token";

/**
 * Routes that must stay reachable without an admin session.
 *
 * `/verify` is the landing page for DOI verification emails: the person opening
 * it is a loyalty member confirming their address, not an admin, so redirecting
 * them to /login would dead-end the flow. It carries no console data - it
 * posts the emailed id/code pair to the API and shows the answer.
 */
const PUBLIC_ROUTES = new Set(["/login", "/verify"]);

/**
 * Auth gate. Runs before every matched route (see `config.matcher`):
 *   - unauthenticated + not on a public route -> redirect to /login
 *   - authenticated     + on /login           -> redirect to /
 *
 * Only reads the signed session cookie - no shared state, per Next.js proxy
 * guidance. Failed-login lockout is handled in the login Server Action.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const authenticated = verifyToken(request.cookies.get(SESSION_COOKIE)?.value);

  if (!authenticated && !PUBLIC_ROUTES.has(pathname)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Only /login is pointless while signed in; an admin may still legitimately
  // open a member's verification link.
  if (authenticated && pathname === "/login") {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Run on all routes except Next internals, static/public assets, and /api/*.
  // The data proxy (/api/le/*) does its own cookie check and returns 401 JSON,
  // so it must not be caught by this HTML login redirect.
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\.svg$|.*\\.png$|.*\\.ico$).*)",
  ],
};
