"""FastAPI routers, one module per resource.

Routers only orchestrate HTTP <-> ORM: request validation (via
``app.schemas``), calling into ``app.services`` for anything beyond a plain
CRUD read/write, and shaping the response. A router never imports another
router - that coupling lives in ``app.services`` instead.
"""
