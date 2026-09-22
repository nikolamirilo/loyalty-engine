"""Challenge tools: gamification challenges members work toward and complete.
Listing/getting a challenge or a member's progress requires the ``read``
scope; creating, updating, deleting a challenge, assigning/unassigning a
member, recording progress, force-completing, and segment bulk-assignment
all require ``write``.
"""

from typing import Any, Dict, List, Optional

from app.client import loyalty_api_client as api
from app.core import annotations as ann
from app.core.auth import require_scope
from app.mcp_instance import mcp


# ── challenge definitions (admin CRUD) ───────────────────────────────────────


@mcp.tool(title="Create Challenge", annotations=ann.WRITE)
async def create_challenge(
    name: str,
    description: Optional[str] = None,
    target_value: int = 1,
    reward_points: int = 0,
    reward_id: Optional[str] = None,
    is_active: bool = True,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    expiry_days: Optional[int] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a challenge. `target_value` is the progress amount needed to
    complete it. `reward_points` and/or `reward_id` (see `list_rewards`) are
    granted on completion. `expires_at` is an absolute campaign deadline;
    `expiry_days` instead gives each member N days from when they're
    assigned - set at most one of the two.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "description": description,
        "target_value": target_value,
        "reward_points": reward_points,
        "reward_id": reward_id,
        "is_active": is_active,
        "starts_at": starts_at,
        "expires_at": expires_at,
        "expiry_days": expiry_days,
    }
    return await api.post("/challenges", body, program=program)


@mcp.tool(title="List Challenges", annotations=ann.READ)
async def list_challenges(
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    program: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List challenges, newest first, optionally restricted to active ones.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        "/challenges",
        params={"active_only": active_only, "skip": skip, "limit": limit},
        program=program,
    )


@mcp.tool(title="Get Challenge", annotations=ann.READ)
async def get_challenge(challenge_id: str, program: Optional[str] = None) -> Dict[str, Any]:
    """Get a single challenge definition by id.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/challenges/{challenge_id}", program=program)


@mcp.tool(title="Update Challenge", annotations=ann.WRITE)
async def update_challenge(
    challenge_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    target_value: Optional[int] = None,
    reward_points: Optional[int] = None,
    reward_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    expiry_days: Optional[int] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a challenge. Only the fields provided are changed; existing
    member assignments and progress are unaffected.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    body = {
        "name": name,
        "description": description,
        "target_value": target_value,
        "reward_points": reward_points,
        "reward_id": reward_id,
        "is_active": is_active,
        "starts_at": starts_at,
        "expires_at": expires_at,
        "expiry_days": expiry_days,
    }
    return await api.patch(f"/challenges/{challenge_id}", body, program=program)


@mcp.tool(title="Delete Challenge", annotations=ann.DELETE)
async def delete_challenge(challenge_id: str, program: Optional[str] = None) -> None:
    """Delete a challenge definition, along with any member assignments on it.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/challenges/{challenge_id}", program=program)


# ── assignment & progress (member-centric) ───────────────────────────────────


@mcp.tool(title="Assign Challenge to Member", annotations=ann.WRITE)
async def assign_challenge_to_member(
    member_id: str,
    challenge_id: str,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Assign a challenge to a member, starting their progress at 0. Fails if
    already assigned, or if the challenge is inactive/expired.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(f"/members/{member_id}/challenges/{challenge_id}", program=program)


@mcp.tool(title="List Member Challenges", annotations=ann.READ)
async def list_member_challenges(
    member_id: str,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    program: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List challenges assigned to a member, newest-assigned first. `status`
    optionally filters to one of: assigned, in_progress, completed, expired,
    cancelled.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(
        f"/members/{member_id}/challenges",
        params={"status": status, "skip": skip, "limit": limit},
        program=program,
    )


@mcp.tool(title="Get Member Challenge Progress", annotations=ann.READ)
async def get_member_challenge_progress(
    member_id: str,
    challenge_id: str,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a challenge's definition merged with one member's progress on it
    (`currentValue`, `progressPercent`, `remaining`, `effectiveStatus`, ...).
    Works whether or not the member has been assigned the challenge yet.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("read")
    return await api.get(f"/members/{member_id}/challenges/{challenge_id}", program=program)


@mcp.tool(title="Update Challenge Progress", annotations=ann.WRITE)
async def update_challenge_progress(
    member_id: str,
    challenge_id: str,
    amount: int = 1,
    description: Optional[str] = None,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Add `amount` to a member's progress on an assigned challenge. If this
    reaches the challenge's `targetValue`, it's completed automatically and
    its reward (points and/or a prize) is granted. Fails if the assignment is
    already completed/cancelled/expired.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        f"/members/{member_id}/challenges/{challenge_id}/progress",
        {"amount": amount, "description": description},
        program=program,
    )


@mcp.tool(title="Complete Challenge for Member", annotations=ann.WRITE)
async def complete_challenge(
    member_id: str,
    challenge_id: str,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Admin force-complete: grants the challenge's reward to the member
    regardless of their current progress or the deadline. Fails if the
    assignment is already completed or cancelled.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(f"/members/{member_id}/challenges/{challenge_id}/complete",
    program=program,
    )


@mcp.tool(title="Remove Challenge from Member", annotations=ann.DELETE)
async def unassign_challenge(
    member_id: str,
    challenge_id: str,
    program: Optional[str] = None,
) -> None:
    """Remove a challenge assignment from a member, discarding their progress.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.delete(f"/members/{member_id}/challenges/{challenge_id}", program=program)


# ── bulk assignment by segment ───────────────────────────────────────────────


@mcp.tool(title="Assign Challenge to Segment", annotations=ann.WRITE)
async def assign_challenge_to_segment(
    challenge_id: str,
    segment_id: str,
    program: Optional[str] = None,
) -> Dict[str, Any]:
    """Assign a challenge to every member currently in a segment (see
    `list_segments`). Members already assigned the challenge are skipped, not
    duplicated or reset. Returns counts of how many were newly `assigned` vs
    `skipped`.

    `program` is the program slug or id to act in; defaults to the server's
    configured program.
    """
    require_scope("write")
    return await api.post(
        f"/challenges/{challenge_id}/assign-segment",
        {"segment_id": segment_id},
        program=program,
    )
