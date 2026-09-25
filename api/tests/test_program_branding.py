"""Regression test for program branding: brand colours and the logo upload.

Covers colour validation and normalisation, clearing a colour back to the
stock theme, the upload's type sniffing and size limit, replacing a logo
(which must delete the old file), removing it, and the clean 503 a deployment
without Storage configured answers with.

Runs against an in-memory SQLite database with an in-memory fake in place of
Supabase Storage. It never touches Supabase.

Run: ./venv/bin/python -m tests.test_program_branding
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@h:6543/postgres")
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("DOI_FROM_EMAIL", "noreply@example.com")

import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

import app.core.database as database

# One shared in-memory connection: SQLite drops the database when the last
# connection closes, and the app's NullPool closes one after every request.
database.engine = sqlalchemy.create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
database.SessionLocal.configure(bind=database.engine)


@compiles(JSONB, "sqlite")
def _jsonb_on_sqlite(type_, compiler, **kw):  # postgres-only type
    return "JSON"


from app.main import app  # noqa: E402 - must be imported after the engine swap
from app.models import Member, MemberAttribute  # noqa: E402
from app.services.storage import get_optional_storage  # noqa: E402

# ...as must these, postgres-only defaults SQLite cannot render.
Member.__table__.c.custom_attributes.server_default = None
MemberAttribute.__table__.c.options.server_default = None
database.Base.metadata.create_all(bind=database.engine)

AUTH = {"Authorization": "Bearer test-token"}
client = TestClient(app, raise_server_exceptions=False)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
SVG = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"></svg>'


class FakeStorage:
    PREFIX = "https://example.supabase.co/storage/v1/object/public/program-assets/"

    def __init__(self) -> None:
        self.files: dict[str, tuple[bytes, str]] = {}

    def upload(self, path: str, data: bytes, content_type: str) -> str:
        self.files[path] = (data, content_type)
        return self.PREFIX + path

    def delete_url(self, url: str) -> None:
        self.files.pop(url.removeprefix(self.PREFIX), None)


failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def put_logo(program_id: str, data: bytes, content_type: str = "image/png"):
    return client.put(
        f"/programs/{program_id}/logo",
        content=data,
        headers={**AUTH, "Content-Type": content_type},
    )


def main() -> None:
    storage = FakeStorage()
    app.dependency_overrides[get_optional_storage] = lambda: storage

    # 1. Colours are accepted as #rrggbb, stored lowercase, and returned in
    # camelCase alongside a null logo.
    created = client.post(
        "/programs",
        json={"name": "Lidl Plus", "isDefault": True, "primaryColor": "#0050AA", "secondaryColor": "#fff000"},
        headers=AUTH,
    )
    check(created.status_code == 201, f"creating a branded program answered {created.status_code}: {created.text}")
    program = created.json()
    pid = program["id"]
    check(program.get("primaryColor") == "#0050aa", f"primary colour was {program.get('primaryColor')!r}")
    check(program.get("secondaryColor") == "#fff000", f"secondary colour was {program.get('secondaryColor')!r}")
    check("logoUrl" in program and program["logoUrl"] is None, f"a new program's logoUrl was {program.get('logoUrl')!r}")

    # 2. Anything but #rrggbb is refused - the client writes it into a stylesheet.
    for bad in ("blue", "#05a", "#0050aa80", "#0050aa;}body{"):
        response = client.patch(f"/programs/{pid}", json={"primaryColor": bad}, headers=AUTH)
        check(response.status_code == 422, f"primaryColor {bad!r} answered {response.status_code}")

    # 3. A PATCH that leaves colours out keeps them; an explicit null clears one,
    # while a null name is still ignored rather than blanking the program.
    kept = client.patch(f"/programs/{pid}", json={"description": "Demo"}, headers=AUTH).json()
    check(kept["primaryColor"] == "#0050aa", "an unrelated edit dropped the primary colour")
    cleared = client.patch(f"/programs/{pid}", json={"secondaryColor": None, "name": None}, headers=AUTH)
    check(cleared.status_code == 200, f"clearing a colour answered {cleared.status_code}: {cleared.text}")
    check(cleared.json()["secondaryColor"] is None, "an explicit null did not clear the secondary colour")
    check(cleared.json()["name"] == "Lidl Plus", "a null name was applied instead of ignored")
    check(cleared.json()["primaryColor"] == "#0050aa", "clearing one colour cleared the other")

    # 4. Uploading stores the file under the program and points logoUrl at it.
    uploaded = put_logo(pid, PNG)
    check(uploaded.status_code == 200, f"uploading a PNG answered {uploaded.status_code}: {uploaded.text}")
    first_url = uploaded.json().get("logoUrl") or ""
    first_path = first_url.removeprefix(FakeStorage.PREFIX)
    check(first_path.startswith(f"programs/{pid}/") and first_path.endswith(".png"), f"logo stored at {first_path!r}")
    check(storage.files.get(first_path, (b"", ""))[1] == "image/png", "the PNG was not stored as image/png")

    # 5. The type comes from the bytes, not the header.
    replaced = put_logo(pid, SVG, content_type="application/octet-stream")
    check(replaced.status_code == 200, f"uploading an SVG answered {replaced.status_code}: {replaced.text}")
    second_url = replaced.json().get("logoUrl") or ""
    check(second_url.endswith(".svg") and second_url != first_url, f"replacement logo URL was {second_url!r}")
    check(first_path not in storage.files, "replacing the logo left the old file behind")

    rejected = put_logo(pid, b"<html>not an image</html>", content_type="image/png")
    check(rejected.status_code == 400, f"an HTML page labelled image/png answered {rejected.status_code}")
    too_big = put_logo(pid, PNG + b"\x00" * (2 * 1024 * 1024))
    check(too_big.status_code == 413, f"a logo over 2 MB answered {too_big.status_code}")
    empty = put_logo(pid, b"")
    check(empty.status_code == 400, f"an empty upload answered {empty.status_code}")
    check(client.get(f"/programs/{pid}", headers=AUTH).json()["logoUrl"] == second_url, "a rejected upload changed the logo")

    # 6. Removing the logo clears the URL and deletes the file.
    removed = client.delete(f"/programs/{pid}/logo", headers=AUTH)
    check(removed.status_code == 200 and removed.json()["logoUrl"] is None, f"removing the logo answered {removed.text}")
    check(not storage.files, f"removing the logo left files behind: {list(storage.files)}")

    # 7. Deleting a program deletes its logo too.
    other = client.post("/programs", json={"name": "Aldi"}, headers=AUTH).json()["id"]
    put_logo(other, PNG)
    check(len(storage.files) == 1, "the second program's logo was not stored")
    check(client.delete(f"/programs/{other}", headers=AUTH).status_code == 204, "deleting a program failed")
    check(not storage.files, "deleting a program left its logo behind")

    # 8. Without Storage configured, uploads answer a clear 503 - and removing a
    # logo still works, since there is then nothing to clean up.
    app.dependency_overrides[get_optional_storage] = lambda: None
    unconfigured = put_logo(pid, PNG)
    check(unconfigured.status_code == 503, f"an upload without Storage answered {unconfigured.status_code}")
    check(client.delete(f"/programs/{pid}/logo", headers=AUTH).status_code == 200, "removing a logo needed Storage")
    app.dependency_overrides.clear()

    if failures:
        print("FAIL:")
        for failure in failures:
            print("  -", failure)
        raise SystemExit(1)
    print("OK: program colours validate and clear, logos upload, replace and delete")


if __name__ == "__main__":
    main()
