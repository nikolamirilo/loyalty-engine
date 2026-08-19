"""Business logic shared across routers.

Anything a router needs that isn't a straight CRUD read/write on its own model
lives here instead of in another router. Previously ``apply_tier`` lived in the
tiers router and four other routers imported it directly (``routers.tiers`` /
``routers.challenges``), which meant every router's import graph doubled as an
undocumented dependency graph. Router -> service -> model is a one-way street:
services never import routers, so there's no cycle to reason about.
"""
