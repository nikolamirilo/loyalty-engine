"""The behaviour hints every tool declares, defined once.

MCP has no category field, so a client cannot be told that `earn_points` is a
"Points" tool. What it *is* told is how a tool behaves, through
`ToolAnnotations`, and that is what a client reads to sort a server's tools
into buckets.

Three presets cover the tools that declare hints, splitting into read, write
and delete. They mirror the `require_scope(...)` call on each tool's first
line, so the hint a client sees and the check the server enforces cannot drift
apart:

| Preset   | `require_scope` | Meaning |
|----------|-----------------|---------|
| `READ`   | `read`          | Looks at data, changes nothing. |
| `WRITE`  | `write`         | Creates or updates, removes nothing. |
| `DELETE` | `write`         | Removes a record. |

`DELETE` is for tools that remove a record and nothing else. A write that
merely spends down a value, `burn_points`, stays `WRITE`: the record it writes
is a new transaction, and nothing is removed.

There is deliberately no preset for the two DOI tools. They declare no
annotations at all, which is what lands them in a client's separate bucket for
unhinted tools - the one place this server can put the only two tools that
reach an address outside it. See `app/tools/doi.py` and "How tools are grouped"
in the README.

These are hints, not enforcement. `require_scope` is the actual gate.
"""

from mcp.types import ToolAnnotations

# `openWorldHint=False` throughout: every tool that declares a preset addresses
# one loyalty API holding a closed, enumerable set of entities, not the open
# internet. The two tools that don't fit that declare nothing at all.

READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)

# `destructiveHint` defaults to true when unset, so the non-destructive writes
# have to say so explicitly rather than leave it off.
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)

DELETE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)
