"""Generate the Loyalty Engine architecture diagram as SVG."""
import sys
from html import escape

W, H = 1680, 1070
out = []
FONT = "Inter, 'DejaVu Sans', Arial, sans-serif"

PAL = {
    "actor": ("#f1f5f9", "#64748b"),
    "client": ("#eef2ff", "#4f46e5"),
    "mcp": ("#f5f3ff", "#7c3aed"),
    "api": ("#eff6ff", "#2563eb"),
    "data": ("#ecfdf5", "#059669"),
    "saas": ("#fff7ed", "#ea580c"),
    "ci": ("#ffffff", "#334155"),
}
INK, MUTED = "#0f172a", "#475569"


def text(x, y, s, size=12.5, weight=400, fill=INK, anchor="start"):
    out.append(
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}">{escape(s)}</text>'
    )


def rect(x, y, w, h, fill, stroke, rx=10, dash=None, sw=1.5):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}"{d}/>'
    )


def box(x, y, w, h, kind, title, sub=None, lines=()):
    fill, stroke = PAL[kind]
    rect(x, y, w, h, fill, stroke)
    rect(x, y, 6, h, stroke, stroke, rx=3, sw=0)
    text(x + 18, y + 26, title, 16, 600)
    yy = y + 46
    if sub:
        text(x + 18, yy, sub, 12, 400, MUTED)
        yy += 20
    for line in lines:
        text(x + 18, yy, line, 12.5)
        yy += 19


def item(x, y, w, s, kind, h=38):
    _, stroke = PAL[kind]
    rect(x, y, w, h, "#ffffff", stroke, rx=7, sw=1)
    text(x + 12, y + h / 2 + 4.5, s, 12.5)


def arrow(d, label=None, lx=0, ly=0, color="#334155", dash=None, anchor="middle"):
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.8"{ds} '
        f'marker-end="url(#arr)"/>'
    )
    if label:
        for i, part in enumerate(label.split("\n")):
            text(lx, ly + i * 14, part, 11, 500, MUTED, anchor)


out.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}" font-family="{FONT}">'
)
out.append(
    '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" '
    'markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
    'fill="#334155"/></marker></defs>'
)
rect(0, 0, W, H, "#ffffff", "#ffffff", rx=0)

text(30, 46, "Loyalty Engine — system architecture", 26, 700)
text(
    30, 72,
    "Three services on Vercel share one Supabase Postgres. Only the Loyalty API opens a "
    "database connection; everything else calls it over HTTPS with a bearer token.",
    14, 400, MUTED,
)

# Actors
box(30, 150, 160, 64, "actor", "Staff", "admin console")
box(30, 250, 160, 64, "actor", "Members", "member app")
box(30, 440, 160, 64, "actor", "AI agents", "Claude, MCP clients")
box(30, 690, 160, 64, "actor", "External systems", "e.g. shop, CRM")

# Vercel group
rect(218, 96, 982, 664, "#f8fafc", "#94a3b8", rx=14, dash="6 5")
text(238, 120, "VERCEL · SERVERLESS FUNCTIONS · REGION dub1 (DUBLIN)", 11.5, 700, MUTED)

# Client
box(330, 136, 380, 270, "client", "Next.js 16 client",
    "admin console /admin · member app / · docs /docs")
for i, s in enumerate([
    "proxy.ts — session gate (HMAC-signed cookies)",
    "Server Components + Server Actions → lib/api.ts",
    "/api/le/* route — same-origin proxy for SWR",
    "API token server-only · no NEXT_PUBLIC_* vars",
]):
    item(350, 206 + i * 48, 340, s, "client")

# MCP
box(330, 450, 380, 250, "mcp", "MCP server (FastMCP)",
    "Streamable HTTP · stateless · /mcp")
for i, s in enumerate([
    "BearerAuthMiddleware — MCP_CLIENT_TOKENS",
    "78 tools · require_scope(read | write | admin)",
    "loyalty_api_client — httpx, 15 s timeout",
]):
    item(350, 520 + i * 48, 340, s, "mcp")

# API
box(800, 136, 370, 600, "api", "Loyalty API (FastAPI)",
    "owns all business logic · camelCase JSON")
api_items = [
    "verify_token — Bearer API_TOKEN",
    "get_program — X-Program-Id (id or slug)",
    "routers/ — validate and shape requests",
    "services/ — rule engine, tiers, points ledger",
    "models/ — SQLAlchemy ORM, NullPool",
    "integrations/ — Resend, Supabase Storage",
]
for i, s in enumerate(api_items):
    item(820, 206 + i * 48, 330, s, "api")
# Exception handlers block
rect(820, 502, 330, 96, "#ffffff", "#dc2626", rx=7, sw=1)
text(832, 522, "Exception handlers (app/main.py)", 12.5, 600, "#b91c1c")
text(832, 542, "DomainError → 400/404/409/413/429/5xx", 12)
text(832, 560, "OperationalError → 503 · IntegrityError → 409", 12)
text(832, 578, "body always { \"detail\": \"...\" }", 12)
item(820, 610, 330, "monitoring.py — Sentry SDK, PII scrubbed", "api")
item(820, 658, 330, "/health — open, for uptime checks", "api")

# Supabase group
rect(1290, 96, 360, 290, "#f0fdf4", "#059669", rx=14, dash="6 5")
text(1306, 120, "SUPABASE · eu-west-1 (IRELAND)", 11.5, 700, "#047857")
box(1310, 136, 320, 126, "data", "Postgres", None, [
    "21 tables, rows scoped by program",
    "Supavisor transaction pooler :6543",
    "TLS required · 10 s connect timeout",
])
box(1310, 282, 320, 84, "data", "Storage", None, ["bucket program-assets (logos)"])

box(1290, 420, 360, 112, "saas", "Resend (email)", None, [
    "DOI codes and links, login codes",
    "prize emails · CI test reports",
])
box(1290, 572, 360, 128, "saas", "Sentry", None, [
    "unhandled 5xx + reported errors",
    "performance traces · tag: program",
    "release = git SHA · env = VERCEL_ENV",
])

# Arrows: callers
arrow("M190,182 H328", "session cookie\nadmin_session", 272, 165)
arrow("M190,282 H328", "session cookie\nmember_session", 272, 265)
arrow("M190,472 H328", "MCP over HTTPS\nclient token", 272, 455)
arrow("M190,722 H770 V700 H798", "HTTPS · Bearer API_TOKEN · POST /events", 480, 740)

# Into the API
arrow("M710,300 H798", "Bearer token\nX-Program-Id", 755, 270)
arrow("M710,616 H798", "service token\nX-Program-Id", 755, 586)

# Out of the API
arrow("M1170,416 H1230 V199 H1308", "SQL", 1270, 191)
arrow("M1170,456 H1250 V324 H1308", "logos", 1280, 316)
arrow("M1170,476 H1288", "email", 1229, 468)
arrow("M1170,629 H1288", "errors, traces", 1229, 621)

# Delivery band
rect(30, 796, 1620, 250, "#f8fafc", "#94a3b8", rx=14, dash="6 5")
text(50, 820, "DELIVERY AND QUALITY", 11.5, 700, MUTED)
box(60, 846, 260, 176, "ci", "Developer", "git commit", [
    "husky pre-commit:",
    "• Python syntax (ast.parse)",
    "• ESLint · tsc --noEmit",
    "• next build",
])
box(380, 846, 230, 176, "ci", "GitHub", "nikolamirilo/loyalty-engine", [
    "push / pull request",
    "path-filtered workflows",
    "one per service",
])
box(670, 846, 590, 176, "ci", "GitHub Actions")
for i, s in enumerate([
    "API tests — pytest flow suite vs Postgres 16 service, latency table",
    "Client checks — ESLint + TypeScript typecheck",
    "MCP checks — compile, import, tool registry + program-arg asserts",
    "Scheduled API tests — daily 07:00 and 13:00 UTC",
]):
    rect(688, 884 + i * 33, 554, 28, "#ffffff", "#334155", rx=6, sw=1)
    text(700, 902.5 + i * 33, s, 12.5)
box(1320, 846, 300, 176, "ci", "Email report", "send_ci_report.py → Resend", [
    "on push, manual and",
    "scheduled runs (not PRs)",
    "subject shows pass / FAILED",
    "latency table + failing log tail",
])
arrow("M320,934 H378", "push", 349, 926)
arrow("M610,934 H668")
arrow("M1260,934 H1318")
arrow("M495,846 V762", "Vercel Git deploy", 505, 790, anchor="start")

out.append("</svg>")
open(sys.argv[1], "w").write("\n".join(out))
