import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth/config";
import { verifyToken } from "@/lib/auth/token";

/**
 * Auth gate. Runs before every matched route (see `config.matcher`):
 *   - unauthenticated + not on /login  -> redirect to /login
 *   - authenticated     + on /login    -> redirect to /
 *
 * Only reads the signed session cookie - no shared state, per Next.js proxy
 * guidance. Failed-login lockout is handled in the login Server Action.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isLoginRoute = pathname === "/login";
  const authenticated = verifyToken(request.cookies.get(SESSION_COOKIE)?.value);

  if (!authenticated && !isLoginRoute) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (authenticated && isLoginRoute) {
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
