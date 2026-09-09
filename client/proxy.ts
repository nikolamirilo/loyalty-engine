import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth/config";
import { verifyToken } from "@/lib/auth/token";
import { MEMBER_SESSION_COOKIE } from "@/lib/memberAuth/config";
import { verifyMemberToken } from "@/lib/memberAuth/token";

/** Routes gated by a member session; anything else under `/` is public. */
const MEMBER_PROTECTED_ROUTES = new Set(["/home", "/products", "/wallet"]);

/**
 * Auth gate. Runs before every matched route (see `config.matcher`) and
 * enforces two independent auth domains that never overlap:
 *
 *   - `/admin/**`   - admin console, gated by the `admin_session` cookie
 *   - everything else - the member app, gated by the `member_session` cookie
 *
 * `/verify` is the landing page for DOI verification emails: the person
 * opening it is a loyalty member confirming their address, not a signed-in
 * member or an admin, so it carries no session data - it posts the emailed
 * id/code pair to the API and shows the answer.
 *
 * Only reads the signed session cookies - no shared state, per Next.js proxy
 * guidance. Failed-login lockout is handled in the login Server Action.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/admin")) {
    const adminAuthenticated = verifyToken(request.cookies.get(SESSION_COOKIE)?.value);

    if (!adminAuthenticated && pathname !== "/admin/login") {
      return NextResponse.redirect(new URL("/admin/login", request.url));
    }
    if (adminAuthenticated && pathname === "/admin/login") {
      return NextResponse.redirect(new URL("/admin", request.url));
    }
    return NextResponse.next();
  }

  if (pathname === "/verify") {
    return NextResponse.next();
  }

  const memberId = verifyMemberToken(request.cookies.get(MEMBER_SESSION_COOKIE)?.value);
  const memberAuthenticated = memberId !== null;

  // `/` is the sign-in/sign-up landing page - pointless once signed in.
  if (pathname === "/") {
    if (memberAuthenticated) {
      return NextResponse.redirect(new URL("/home", request.url));
    }
    return NextResponse.next();
  }

  if (MEMBER_PROTECTED_ROUTES.has(pathname) && !memberAuthenticated) {
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
