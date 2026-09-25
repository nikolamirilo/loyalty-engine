"""Program discovery: which loyalty programs exist, so a caller can pick one.

The only tools here that are not program-scoped, mirroring the loyalty API's
own ``/programs`` router - this is how a caller finds out what it may pass as
the ``program`` argument everywhere else, so it cannot itself require one.

Creating and editing a program require ``write``. Deleting one is left out on
purpose and always will be: it cascades through every member, balance and
rule in the program, so it stays a manual action in the admin console.
"""

from typing import Any, Dict, List, Optional

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


@mcp.tool(title="Create Program", annotations=ann.WRITE)
async def create_program(
    name: str,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    is_default: bool = False,
) -> Dict[str, Any]:
    """Create a loyalty program. `slug` (lowercase letters, digits and single
    hyphens) is what other tools accept as `program`; omit it to derive one
    from `name`. `is_default` true makes this the program used when `program`
    is omitted, taking that over from the current default.

    Members are shared across programs, so every existing member is enrolled
    in the new program straight away, at zero points.
    """
    require_scope("write")
    body = {"name": name, "slug": slug, "description": description, "is_default": is_default}
    return await api.post("/programs", body)


@mcp.tool(title="Update Program", annotations=ann.WRITE)
async def update_program(
    program_id: str,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    is_default: Optional[bool] = None,
) -> Dict[str, Any]:
    """Update a program by UUID. Only the fields provided are changed.

    Changing `slug` breaks any caller still passing the old one as `program`.
    `is_default` can only be set to true: to move the default, make another
    program the default rather than unsetting this one.
    """
    require_scope("write")
    body = {"name": name, "slug": slug, "description": description, "is_default": is_default}
    return await api.patch(f"/programs/{program_id}", body)
