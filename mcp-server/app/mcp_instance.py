"""The shared FastMCP instance every tool module registers onto.

Kept in its own module (rather than inside ``app/server.py``) so tool
modules can ``from app.mcp_instance import mcp`` without importing
``app/server.py`` - which is what imports the tool modules - and risking a
circular import.

``stateless_http=True`` because this server runs as a hosted, potentially
serverless HTTP endpoint: each request is handled independently rather than
relying on sticky server-side session state between calls.
"""

from mcp.server import MCPServer

from app.core.config import settings

mcp = MCPServer(
    name=settings.project_name,
)
