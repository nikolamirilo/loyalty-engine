"""Errors the business logic raises, independent of HTTP.

Services and integrations raise these instead of FastAPI's ``HTTPException``,
so they stay free of the web framework and can be called from scripts and the
rule engine without knowing about status codes. ``app.main`` turns each one
into a response with the status below and the same ``{"detail": ...}`` body
FastAPI uses for ``HTTPException``, so API callers see no difference.

Routers and request dependencies (``app.core.program``, ``app.core.security``)
are the HTTP layer and keep raising ``HTTPException`` directly.
"""


class DomainError(Exception):
    """Base class. ``status_code`` is only read by the handler in ``app.main``."""

    status_code = 400

    def __init__(self, detail: str, *, headers: dict[str, str] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.headers = headers


class InvalidInput(DomainError):
    """The request breaks a business rule the schema can't express."""

    status_code = 400


class NotFound(DomainError):
    status_code = 404


class Conflict(DomainError):
    """The request clashes with the current state, e.g. an email already verified."""

    status_code = 409


class PayloadTooLarge(DomainError):
    status_code = 413


class RateLimited(DomainError):
    status_code = 429

    def __init__(self, detail: str, *, retry_after: int) -> None:
        super().__init__(detail, headers={"Retry-After": str(retry_after)})


class Misconfigured(DomainError):
    """The deployment is set up wrong. Retrying can't help; a human has to fix it."""

    status_code = 500


class UpstreamError(DomainError):
    """An external service (email, file storage) failed or could not be reached."""

    status_code = 502


class FeatureUnavailable(DomainError):
    """An optional feature is off because its settings are missing."""

    status_code = 503
