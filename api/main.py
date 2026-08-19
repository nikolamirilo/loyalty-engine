"""Backwards-compatible entry point.

The app now lives in `app/` (see app/main.py and README.md - Project layout).
This shim exists only so `uvicorn main:app` and any external deploy config
pointing at `api/main.py` keep working unchanged.
"""

from app.main import app

__all__ = ["app"]
