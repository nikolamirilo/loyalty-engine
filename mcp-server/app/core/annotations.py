"""The behaviour hints every tool declares, defined once.

MCP has no category field, so a client cannot be told that `earn_points` is a
"Points" tool. What it *is* told is how a tool behaves, through
`ToolAnnotations`, and that is what a client reads to sort a server's tools
into buckets. A tool that declares nothing has nothing to sort by, so it falls
into a flat **Other tools** list.

Four presets cover every tool here, splitting into read, write and delete.
They mirror the `require_scope(...)` call on each tool's first line, so the
hint a client sees and the check the server enforces cannot drift apart:

| Preset     | `require_scope` | Meaning |
|------------|-----------------|---------|
| `READ`     | `read`          | Looks at data, changes nothing. |
| `WRITE`    | `write`         | Creates or updates, removes nothing. |
| `DELETE`   | `write`         | Removes a record. |
| `OUTBOUND` | `write`         | Reaches a real inbox outside the system. |

`DELETE` is for tools that remove a record and nothing else. A write that
merely spends down a value, `burn_points`, stays `WRITE`: the record it writes
is a new transaction, and nothing is removed.

These are hints, not enforcement. `require_scope` is the actual gate.
"""

from mcp.types import ToolAnnotations

# `openWorldHint=False` on all but OUTBOUND: these tools address one loyalty
# API holding a closed, enumerable set of entities, not the open internet.

READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)

# `destructiveHint` defaults to true when unset, so the non-destructive writes
# have to say so explicitly rather than leave it off.
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)

DELETE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)

OUTBOUND = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
