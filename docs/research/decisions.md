# Scope decisions

Agreed with the product owner on 2026-10-23.

- **Product name**: Loyalty Simulator (the name shown in the admin sidebar and on the landing page).
- **Audience**: staff who run a program in the admin console (main focus), plus a shorter module
  for members using the member app (sign in, home, products, wallet, account, email verification,
  prize claim).
- **Delivery**: one self-contained HTML page served by the client app at the public route `/docs`
  (no session needed, like `/verify`).
- **MCP server**: left out. It is a developer integration, not something a user clicks through.
- **Feature flags**: the client has none (no `NEXT_PUBLIC_*` variables, no flag client).
- **Hidden or internal**: `/admin/test-btn` is a leftover scratch page and is left out. The REST API
  itself (Swagger) is out of scope: these are end-user docs, not an API reference.
