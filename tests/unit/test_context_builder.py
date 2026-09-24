from __future__ import annotations

from pathlib import Path

from guardian.context_builder import ContextBuilder
from models import ChangedFile, PullRequest


def make_pull_request(
    *,
    changed_files: list[ChangedFile],
) -> PullRequest:
    return PullRequest(
        repository_owner="example",
        repository_name="project",
        number=42,
        title="Synthetic contextual review",
        description="Synthetic PR used by context builder tests.",
        base_branch="main",
        head_branch="feature/context",
        base_sha="base123",
        head_sha="head456",
        additions=sum(
            file.additions
            for file in changed_files
        ),
        deletions=sum(
            file.deletions
            for file in changed_files
        ),
        changed_files_count=len(
            changed_files
        ),
        commit_count=1,
        changed_files=changed_files,
    )


def changed_file(
    filename: str,
    *,
    patch: str = "",
) -> ChangedFile:
    return ChangedFile(
        filename=filename,
        status="modified",
        additions=1,
        deletions=1,
        changes=2,
        patch=patch,
    )


def write_file(
    root: Path,
    relative_path: str,
    content: str,
) -> Path:
    path = (
        root
        / relative_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def test_context_builder_reads_repository_structure(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/services/users.py",
        """
def find_user(user_id):
    return user_id
""",
    )

    write_file(
        repository,
        "app/routes/users.py",
        """
from app.services.users import find_user
""",
    )

    write_file(
        repository,
        "tests/test_users.py",
        """
def test_find_user():
    assert True
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/services/users.py"
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    assert (
        context.repository.repository_files
        >= 3
    )


def test_context_builder_identifies_changed_file_context(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/services/users.py",
        """
def normalize_user(name):
    return name.strip()
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/services/users.py",
                patch="""
-def normalize_user(name):
-    return name
+def normalize_user(name):
+    return name.strip()
""",
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    filenames = {
        item.filename
        for item in context.changed_files
    }

    assert (
        "app/services/users.py"
        in filenames
    )


def test_context_builder_finds_python_dependents(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/services/users.py",
        """
def find_user(user_id):
    return {"id": user_id}
""",
    )

    write_file(
        repository,
        "app/routes/users.py",
        """
from app.services.users import find_user


def get_user(user_id):
    return find_user(user_id)
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/services/users.py"
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    assert any(
        "app/routes/users.py"
        in affected
        for affected
        in context.potentially_affected_files
    )


def test_context_builder_detects_api_specification(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "openapi.yaml",
        """
openapi: 3.0.0
info:
  title: Example API
  version: 1.0.0
paths: {}
""",
    )

    write_file(
        repository,
        "app/routes/users.py",
        """
def list_users():
    pass
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/routes/users.py"
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    assert (
        context.repository.api_specs
    )


def test_context_builder_detects_database_migrations(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "migrations/001_create_users.sql",
        """
CREATE TABLE users (
    id INTEGER PRIMARY KEY
);
""",
    )

    write_file(
        repository,
        "app/models.py",
        """
class User:
    pass
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/models.py"
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    assert (
        context.repository.migrations
    )


def test_context_builder_detects_test_files(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/service.py",
        """
def calculate():
    return 42
""",
    )

    write_file(
        repository,
        "tests/test_service.py",
        """
def test_calculate():
    assert True
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/service.py"
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    assert (
        context.repository.test_files
    )


def test_context_builder_detects_security_risk_signals(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/auth.py",
        """
def decode_token(token):
    return jwt.decode(token, SECRET_KEY)
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/auth.py",
                patch="""
+token = request.headers.get("Authorization")
+payload = jwt.decode(token, SECRET_KEY)
""",
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    signals = " ".join(
        context.risk_signals
    ).lower()

    assert (
        "auth" in signals
        or "token" in signals
        or "jwt" in signals
    )


def test_context_builder_detects_database_risk_signals(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/repositories/users.py",
        """
def find_user(email):
    return database.execute(
        f"SELECT * FROM users WHERE email = '{email}'"
    )
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/repositories/users.py",
                patch="""
+query = f"SELECT * FROM users WHERE email = '{email}'"
""",
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    signals = " ".join(
        context.risk_signals
    ).lower()

    assert (
        "sql" in signals
        or "database" in signals
        or "query" in signals
    )


def test_context_builder_detects_queue_components(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "workers/report_worker.py",
        """
from rq import Queue


def process_report(report_id):
    pass
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "workers/report_worker.py",
                patch="""
+from rq import Queue
+queue.enqueue(process_report, report_id)
""",
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    signals = " ".join(
        context.risk_signals
    ).lower()

    assert (
        "queue" in signals
        or "worker" in signals
        or "rq" in signals
    )


def test_context_builder_finds_changed_symbols(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/services/reports.py",
        """
class ReportService:
    def find_report(self, report_id):
        return report_id


def normalize_title(value):
    return value.strip()
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/services/reports.py",
                patch="""
 def normalize_title(value):
-    return value
+    return value.strip()
""",
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    file_context = next(
        item
        for item in context.changed_files
        if (
            item.filename
            == "app/services/reports.py"
        )
    )

    symbol_names = {
        symbol.name
        for symbol
        in file_context.changed_symbols
    }

    assert (
        "normalize_title"
        in symbol_names
        or file_context.changed_symbols
    )


def test_context_builder_goes_beyond_changed_files(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/repositories/reports.py",
        """
def find_report(report_id):
    return report_id
""",
    )

    write_file(
        repository,
        "app/services/reports.py",
        """
from app.repositories.reports import find_report


def get_report(report_id):
    return find_report(report_id)
""",
    )

    write_file(
        repository,
        "app/routes/reports.py",
        """
from app.services.reports import get_report


def route(report_id):
    return get_report(report_id)
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/repositories/reports.py"
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    changed = {
        file.filename
        for file in context.changed_files
    }

    affected = set(
        context.potentially_affected_files
    )

    assert (
        "app/repositories/reports.py"
        in changed
    )

    assert (
        affected
        - changed
    )


def test_context_builder_serializes_to_dictionary(
    tmp_path: Path,
):
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    write_file(
        repository,
        "app/service.py",
        """
def execute():
    return True
""",
    )

    pull_request = make_pull_request(
        changed_files=[
            changed_file(
                "app/service.py"
            )
        ]
    )

    context = ContextBuilder().build(
        pull_request,
        repository,
    )

    payload = context.to_dict()

    assert isinstance(
        payload,
        dict,
    )

    assert (
        payload["pr_id"]
        == pull_request.identifier
    )

    assert (
        "repository"
        in payload
    )

    assert (
        "changed_files"
        in payload
    )

    assert (
        "risk_signals"
        in payload
    )