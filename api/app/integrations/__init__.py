"""Adapters for the external services the API talks to.

Each module wraps one provider (Resend for email, Supabase Storage for files)
behind a small interface, and turns that provider's failures into
``app.core.errors`` so services never handle a provider's own exceptions.
Business logic lives in ``app.services`` and calls in here, never the other
way round.
"""
