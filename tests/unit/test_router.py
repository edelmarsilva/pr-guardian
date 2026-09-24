from __future__ import annotations

import pytest

from guardian.router import (
    ReviewDomain,
    ReviewerRouter,
)
from models import ChangedFile, PullRequest


def make_pull_request(
    files: list[ChangedFile],
) -> PullRequest:
    return PullRequest(
        repository_owner="example",
        repository_name="project",
        number=42,
        title="Synthetic benchmark PR",
        description="Synthetic Pull Request used for router tests.",
        base_branch="main",
        head_branch="feature/test",
        base_sha="base123",
        head_sha="head456",
        additions=sum(
            file.additions
            for file in files
        ),
        deletions=sum(
            file.deletions
            for file in files
        ),
        changed_files_count=len(
            files
        ),
        commit_count=1,
        changed_files=files,
    )


def changed_file(
    filename: str,
    *,
    patch: str = "",
    status: str = "modified",
    additions: int = 1,
    deletions: int = 0,
) -> ChangedFile:
    return ChangedFile(
        filename=filename,
        status=status,
        additions=additions,
        deletions=deletions,
        changes=additions + deletions,
        patch=patch,
    )


def selected_domains(
    pull_request: PullRequest,
) -> set[ReviewDomain]:
    result = ReviewerRouter().route(
        pull_request
    )

    return set(
        result.selected_reviewers
    )


def test_readme_only_change_does_not_select_all_reviewers():
    pull_request = make_pull_request(
        [
            changed_file(
                "README.md",
                patch="""
+## Installation
+
+Run pip install -r requirements.txt.
""",
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.SECURITY not in domains
    assert ReviewDomain.DATABASE not in domains
    assert ReviewDomain.QUEUE not in domains
    assert ReviewDomain.API not in domains


def test_python_source_change_selects_code_review():
    pull_request = make_pull_request(
        [
            changed_file(
                "app/services/users.py",
                patch="""
 def find_user(user_id):
-    return repository.find(user_id)
+    return repository.find_active(user_id)
""",
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.CODE in domains


def test_production_code_change_selects_test_impact():
    pull_request = make_pull_request(
        [
            changed_file(
                "app/services/payments.py",
                patch="""
 def charge(amount):
+    validate_amount(amount)
     return gateway.charge(amount)
""",
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.TEST in domains


@pytest.mark.parametrize(
    "filename,patch",
    [
        (
            "app/auth.py",
            """
+def validate_token(token):
+    return jwt.decode(token, SECRET_KEY)
""",
        ),
        (
            "app/routes/admin.py",
            """
+if current_user.role == "admin":
+    return sensitive_data()
""",
        ),
        (
            "app/services/reports.py",
            """
+organization_id = current_user.organization_id
+report = repository.get_by_id(report_id)
""",
        ),
    ],
)
def test_security_sensitive_changes_select_security_review(
    filename: str,
    patch: str,
):
    pull_request = make_pull_request(
        [
            changed_file(
                filename,
                patch=patch,
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.SECURITY in domains


@pytest.mark.parametrize(
    "filename",
    [
        "migrations/001_add_users.sql",
        "alembic/versions/123_add_column.py",
        "app/models/user.py",
        "app/repositories/users.py",
    ],
)
def test_database_related_files_select_database_review(
    filename: str,
):
    pull_request = make_pull_request(
        [
            changed_file(
                filename,
                patch="""
+SELECT * FROM users;
""",
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.DATABASE in domains


@pytest.mark.parametrize(
    "filename,patch",
    [
        (
            "app/routes/users.py",
            """
+@users_bp.get("/users/<int:user_id>")
+def get_user(user_id):
+    return jsonify(service.find(user_id))
""",
        ),
        (
            "openapi.yaml",
            """
+paths:
+  /users:
+    get:
+      responses:
+        "200":
+          description: OK
""",
        ),
        (
            "api/swagger.json",
            """
+"paths": {
+  "/reports": {}
+}
""",
        ),
    ],
)
def test_api_related_changes_select_api_review(
    filename: str,
    patch: str,
):
    pull_request = make_pull_request(
        [
            changed_file(
                filename,
                patch=patch,
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.API in domains


@pytest.mark.parametrize(
    "filename,patch",
    [
        (
            "workers/email_worker.py",
            """
+def send_email_job(payload):
+    send_email(payload)
""",
        ),
        (
            "tasks.py",
            """
+@celery.task
+def process_payment(payment_id):
+    pass
""",
        ),
        (
            "app/jobs.py",
            """
+queue.enqueue(process_report, report_id)
""",
        ),
        (
            "worker.py",
            """
+from rq import Worker
""",
        ),
    ],
)
def test_queue_changes_select_queue_review(
    filename: str,
    patch: str,
):
    pull_request = make_pull_request(
        [
            changed_file(
                filename,
                patch=patch,
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.QUEUE in domains


def test_migration_change_selects_database_and_test_review():
    pull_request = make_pull_request(
        [
            changed_file(
                "migrations/002_add_email.sql",
                patch="""
+ALTER TABLE users
+ADD COLUMN email TEXT NOT NULL;
""",
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.DATABASE in domains
    assert ReviewDomain.TEST in domains


def test_tenant_authorization_change_selects_expected_specialists():
    pull_request = make_pull_request(
        [
            changed_file(
                "app/routes/reports.py",
                patch="""
 organization_id = current_user.organization_id

-report = repository.get_by_id(
-    report_id,
-    organization_id,
-)
+report = repository.get_by_id(
+    report_id,
+)
""",
            ),
            changed_file(
                "app/repositories/reports.py",
                patch="""
-def get_by_id(report_id, organization_id):
+def get_by_id(report_id):
     return db.query(
-        report_id=report_id,
-        organization_id=organization_id,
+        report_id=report_id,
     )
""",
            ),
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.CODE in domains
    assert ReviewDomain.SECURITY in domains
    assert ReviewDomain.TEST in domains
    assert ReviewDomain.DATABASE in domains
    assert ReviewDomain.API in domains

    assert ReviewDomain.QUEUE not in domains


def test_router_exposes_reasons_for_selected_reviewers():
    pull_request = make_pull_request(
        [
            changed_file(
                "app/auth.py",
                patch="""
+token = request.headers.get("Authorization")
+jwt.decode(token, SECRET_KEY)
""",
            )
        ]
    )

    result = ReviewerRouter().route(
        pull_request
    )

    security_decision = next(
        decision
        for decision in result.decisions
        if (
            decision.reviewer
            == ReviewDomain.SECURITY
        )
    )

    assert security_decision.selected is True
    assert security_decision.reasons
    assert (
        security_decision.matched_files
        or security_decision.matched_signals
    )


def test_router_returns_decision_for_every_available_domain():
    pull_request = make_pull_request(
        [
            changed_file(
                "README.md"
            )
        ]
    )

    result = ReviewerRouter().route(
        pull_request
    )

    decided_domains = {
        decision.reviewer
        for decision in result.decisions
    }

    assert decided_domains == set(
        ReviewDomain
    )


def test_router_does_not_select_queue_for_unrelated_python_change():
    pull_request = make_pull_request(
        [
            changed_file(
                "app/utils/formatting.py",
                patch="""
+def normalize_name(value):
+    return value.strip().lower()
""",
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.QUEUE not in domains


def test_router_does_not_select_database_for_pure_frontend_change():
    pull_request = make_pull_request(
        [
            changed_file(
                "app/static/app.js",
                patch="""
+document.querySelector("#submit")
+    .addEventListener("click", submitForm);
""",
            )
        ]
    )

    domains = selected_domains(
        pull_request
    )

    assert ReviewDomain.DATABASE not in domains