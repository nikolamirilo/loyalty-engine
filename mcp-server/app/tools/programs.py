"""Program discovery: which loyalty programs exist, so a caller can pick one.

The only tools here that are not program-scoped, mirroring the loyalty API's
own ``/programs`` router - this is how a caller finds out what it may pass as
the ``program`` argument everywhere else, so it cannot itself require one.

Read-only. Creating, renaming and deleting programs changes the shape of the
whole deployment, so it stays in the admin console rather than being
reachable by an agent.
"""

from typing import Any, Dict, List

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


@mcp.tool(title="List Programs", annotations=ann.READ)
async def list_programs() -> List[Dict[str, Any]]:
    """List the loyalty programs on this deployment, oldest first.

    Call this first when the user has not said which program to work in, then
    pass the chosen program's `slug` as the `program` argument to every other
    tool - members, points, rewards, challenges and the rest are all scoped to
    one program, and the same member can hold a different balance in each.

    The program with `isDefault` true is the one used when `program` is
    omitted. Each entry has `id`, `name`, `slug`, `description`, `isDefault`
    and `createdAt`.
    """
    require_scope("read")
    return await api.get("/programs")


@mcp.tool(title="Get Program", annotations=ann.READ)
async def get_program(program_id: str) -> Dict[str, Any]:
    """Get a single program by id.

    Takes the program's UUID specifically, not its slug - use `list_programs`
    to look one up by name. Other tools' `program` argument accepts either.
    """
    require_scope("read")
    return await api.get(f"/programs/{program_id}")
