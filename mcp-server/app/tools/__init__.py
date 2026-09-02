"""Importing this package registers every tool module's ``@mcp.tool()`` calls
onto the shared FastMCP instance (``app.mcp_instance.mcp``). ``app.server``
imports this package for that side effect - nothing here is meant to be
imported directly by name.
"""

from app.tools import doi, members, points, redemptions, rewards, segments, tiers  # noqa: F401
