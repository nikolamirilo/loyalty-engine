import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/lib/auth/config";
import { verifyToken } from "@/lib/auth/token";
import { UPSTREAM_BASE_URL, UPSTREAM_TOKEN } from "@/lib/server/upstream";

/**
 * Same-origin proxy to the Loyalty Engine API for browser (SWR) calls.
 *
 * The API bearer token is server-only, so the browser can't call the API
 * directly. Instead it calls `/api/le/<path>` and this handler attaches the
 * token server-side and forwards upstream — the token never reaches the client
 * and there is no CORS to manage.
 *
 * Gated on the same signed session cookie as the rest of the console, so it is
 * not an open relay to the backend. Unauthenticated calls get 401 JSON (which
 * `fetch` surfaces to SWR) rather than an HTML login redirect.
 */

export const dynamic = "force-dynamic";

const MAX_ATTEMPTS = 3;
const RETRY_BASE_MS = 150;
/** Transient upstream statuses worth retrying (matches lib/api.ts). */
const RETRY_STATUSES = new Set([500, 502, 503, 504]);

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function proxy(request: NextRequest, path: string[]): Promise<Response> {
  if (!verifyToken(request.cookies.get(SESSION_COOKIE)?.value)) {
    return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
  }

  // Rebuild the upstream URL from the encoded path segments (no traversal) plus
  // the original query string.
  const target = new URL(
    `${UPSTREAM_BASE_URL}/${path.map(encodeURIComponent).join("/")}`,
  );
  target.search = request.nextUrl.search;

  const method = request.method;
  const hasBody = method !== "GET" && method !== "HEAD";
  const body = hasBody ? await request.text() : undefined;

  const headers: Record<string, string> = {
    Accept: "application/json",
    Authorization: `Bearer ${UPSTREAM_TOKEN}`,
  };
  const contentType = request.headers.get("content-type");
  if (hasBody && contentType) headers["Content-Type"] = contentType;

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    let upstream: Response;
    try {
      upstream = await fetch(target, {
        method,
        headers,
        body,
        cache: "no-store",
      });
    } catch {
      if (attempt < MAX_ATTEMPTS) {
        await sleep(RETRY_BASE_MS * 2 ** (attempt - 1));
        continue;
      }
      return NextResponse.json(
        { detail: `Cannot reach the API at ${UPSTREAM_BASE_URL}.` },
        { status: 502 },
      );
    }

    if (RETRY_STATUSES.has(upstream.status) && attempt < MAX_ATTEMPTS) {
      await upstream.body?.cancel();
      await sleep(RETRY_BASE_MS * 2 ** (attempt - 1));
      continue;
    }

    // Forward the upstream response through faithfully (status + JSON body).
    const responseHeaders = new Headers();
    const upstreamContentType = upstream.headers.get("content-type");
    if (upstreamContentType) {
      responseHeaders.set("content-type", upstreamContentType);
    }
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  }

  /* istanbul ignore next: the loop always returns above. */
  return NextResponse.json({ detail: "Request failed." }, { status: 502 });
}

type RouteContext = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, ctx: RouteContext) {
  return proxy(request, (await ctx.params).path);
}
export async function POST(request: NextRequest, ctx: RouteContext) {
  return proxy(request, (await ctx.params).path);
}
export async function PUT(request: NextRequest, ctx: RouteContext) {
  return proxy(request, (await ctx.params).path);
}
export async function PATCH(request: NextRequest, ctx: RouteContext) {
  return proxy(request, (await ctx.params).path);
}
export async function DELETE(request: NextRequest, ctx: RouteContext) {
  return proxy(request, (await ctx.params).path);
}
