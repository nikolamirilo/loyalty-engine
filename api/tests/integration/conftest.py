"""Fixtures for the API flow tests, plus the latency report they produce.

These tests create, mutate and delete real rows. They refuse to run unless
``TEST_DATABASE_URL`` is set, so pointing them at the database in ``api/.env``
takes a deliberate act rather than a forgotten export.

Every request is timed. What is measured is server side handling time, the
whole ASGI stack including routing, auth, the handler and the database round
trip, but not network transfer, since the app is called in process. That is the
part worth tracking: localhost network time would be noise.
"""

import os
import re
import time
from dataclasses import dataclass

import pytest

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

# app.core.config reads these at import time. Set them before anything imports
# the app. load_dotenv() does not overwrite variables that already exist, so
# api/.env cannot quietly replace the test database here.
if TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")

_UUID = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


@dataclass
class Call:
    step: str
    method: str
    route: str
    status: int
    ms: float


CALLS: list[Call] = []

# Test name (without the `test_` prefix) -> passed / failed / skipped. The
# report marks rows by their test's outcome rather than by status code, since a
# test can legitimately assert a 404, and a red mark there would read as a
# failure in a green run.
OUTCOMES: dict[str, str] = {}


def pytest_runtest_logreport(report):
    if report.when == "call":
        OUTCOMES[report.nodeid.rpartition("::")[2].removeprefix("test_")] = report.outcome


class MeasuredClient:
    """Test client that attaches the bearer token, times each call and records it.

    Concrete ids in the path are collapsed back to `{id}` so the report shows
    the route rather than one row per generated UUID.
    """

    def __init__(self, client, token: str):
        self._client = client
        self._headers = {"Authorization": f"Bearer {token}"}
        self.step = ""

    def request(self, method: str, path: str, **kwargs):
        started = time.perf_counter()
        response = self._client.request(method, path, headers=self._headers, **kwargs)
        elapsed_ms = (time.perf_counter() - started) * 1000
        CALLS.append(
            Call(self.step, method, _UUID.sub("{id}", path), response.status_code, elapsed_ms)
        )
        return response

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def patch(self, path, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)


@pytest.fixture(scope="session")
def api():
    if not TEST_DATABASE_URL:
        pytest.fail(
            "TEST_DATABASE_URL is not set. These tests write and delete rows, so "
            "they will not fall back to DATABASE_URL. Point it at a throwaway "
            "database, for example "
            "postgresql://postgres:postgres@localhost:5432/loyalty_test?sslmode=disable",
            pytrace=False,
        )

    from fastapi.testclient import TestClient

    from app.main import app

    # The context manager runs the lifespan, which creates the tables.
    with TestClient(app) as client:
        yield MeasuredClient(client, os.environ["API_TOKEN"])


@pytest.fixture(scope="session")
def state() -> dict:
    """Ids handed from one step to the next."""
    return {}


@pytest.fixture(autouse=True)
def _label_calls(request, api):
    """Tag every call with the test that made it, for the report."""
    api.step = request.node.name.removeprefix("test_")


def _format_table(rows: list[list[str]], headers: list[str], align_right: set[int]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def line(cells):
        out = []
        for i, cell in enumerate(cells):
            out.append(cell.rjust(widths[i]) if i in align_right else cell.ljust(widths[i]))
        return "  ".join(out).rstrip()

    return "\n".join([line(headers), line(["-" * w for w in widths]), *(line(r) for r in rows)])


def _markdown_table(rows: list[list[str]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def pytest_terminal_summary(terminalreporter):
    """Print the latency table, and add it to the GitHub Actions run summary."""
    if not CALLS:
        return

    headers = ["Step", "Method", "Route", "Status", "Latency", "Result"]
    rows = [
        [
            c.step,
            c.method,
            c.route,
            str(c.status),
            f"{c.ms:.1f} ms",
            _TERMINAL_RESULT.get(OUTCOMES.get(c.step, ""), "?"),
        ]
        for c in CALLS
    ]
    total = sum(c.ms for c in CALLS)
    slowest = max(CALLS, key=lambda c: c.ms)
    footer = (
        f"{len(CALLS)} calls, {total:.1f} ms total, "
        f"slowest {slowest.method} {slowest.route} at {slowest.ms:.1f} ms"
    )

    terminalreporter.write_sep("=", "API latency")
    terminalreporter.write_line(_format_table(rows, headers, align_right={3, 4}))
    terminalreporter.write_line("")
    terminalreporter.write_line(footer)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    md_rows = [
        [
            c.step,
            f"`{c.method}`",
            f"`{c.route}`",
            str(c.status),
            f"{c.ms:.1f} ms",
            _MARKDOWN_RESULT.get(OUTCOMES.get(c.step, ""), ""),
        ]
        for c in CALLS
    ]
    with open(summary_path, "a", encoding="utf-8") as fh:
        fh.write("\n## API test results\n\n")
        fh.write(_markdown_table(md_rows, headers) + "\n\n")
        fh.write(
            f"{len(CALLS)} calls, **{total:.1f} ms** total, "
            f"slowest `{slowest.method} {slowest.route}` at **{slowest.ms:.1f} ms**\n"
        )


_TERMINAL_RESULT = {"passed": "ok", "failed": "FAIL", "skipped": "skip"}
_MARKDOWN_RESULT = {
    "passed": ":white_check_mark:",
    "failed": ":x:",
    "skipped": ":fast_forward:",
}
