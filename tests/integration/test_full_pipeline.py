from __future__ import annotations

import json
from pathlib import Path

from scripts.finalize_review import finalize_review


def write_json(
    path: Path,
    payload: dict,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )


def create_repository(
    root: Path,
) -> Path:
    repository = (
        root
        / "workspace"
        / "repositories"
        / "example-project-pr-42"
    )

    repository.mkdir(
        parents=True,
    )

    app_directory = (
        repository
        / "app"
    )

    app_directory.mkdir()

    (
        app_directory
        / "repositories.py"
    ).write_text(
        """
def get_report(report_id):
    return {
        "id": report_id,
        "organization_id": 200,
    }
""",
        encoding="utf-8",
    )

    return repository


def create_review_plan(
    root: Path,
    repository: Path,
) -> Path:
    reports = (
        root
        / "reports"
    )

    plan = {
        "pr_id": "example-project-pr-42",
        "repository": "example/project",
        "pull_number": 42,
        "title": "Remove organization filter",
        "description": (
            "Synthetic Pull Request used "
            "for integration testing."
        ),
        "base_sha": "base123",
        "head_sha": "head456",
        "workspace_path": str(
            repository
        ),
        "changed_files": [
            {
                "filename": (
                    "app/repositories.py"
                ),
                "status": "modified",
                "additions": 3,
                "deletions": 5,
            }
        ],
        "risk_signals": [
            "authorization",
            "tenant",
        ],
        "potentially_affected_files": [
            "app/routes.py",
            "tests/test_reports.py",
        ],
        "selected_reviewers": [
            "code-review",
            "security-review",
        ],
        "skipped_reviewers": [
            "architecture-review",
            "database-review",
            "api-review",
            "queue-review",
            "test-impact",
        ],
    }

    path = (
        reports
        / "raw"
        / "example-project-pr-42"
        / "review-plan.json"
    )

    write_json(
        path,
        plan,
    )

    return reports


def create_reviewer_findings(
    reports: Path,
) -> None:
    pr_id = (
        "example-project-pr-42"
    )

    security = {
        "reviewer": "security-review",
        "findings": [
            {
                "id": "SEC-001",
                "category": (
                    "TENANT_ISOLATION"
                ),
                "severity": "HIGH",
                "confidence": "CONFIRMED",
                "title": (
                    "Report lookup is not "
                    "scoped by organization"
                ),
                "description": (
                    "The repository lookup "
                    "uses report_id without "
                    "organization_id."
                ),
                "file": (
                    "app/repositories.py"
                ),
                "line": 1,
                "evidence": [
                    (
                        "get_report accepts "
                        "only report_id."
                    ),
                    (
                        "organization scope "
                        "is absent from the "
                        "lookup."
                    ),
                ],
                "impact": (
                    "A tenant may access "
                    "another tenant's report."
                ),
                "recommendation": (
                    "Scope report retrieval "
                    "using the authenticated "
                    "organization."
                ),
                "verification_status": (
                    "UNVERIFIED"
                ),
                "origin": (
                    "INTRODUCED_BY_PR"
                ),
                "metadata": {
                    "root_cause": (
                        "missing organization "
                        "scope"
                    )
                },
            }
        ],
    }

    code = {
        "reviewer": "code-review",
        "findings": [
            {
                "id": "CODE-001",
                "category": (
                    "LOGIC_ERROR"
                ),
                "severity": "HIGH",
                "confidence": "CONFIRMED",
                "title": (
                    "Organization scope is "
                    "ignored"
                ),
                "description": (
                    "The changed repository "
                    "contract no longer "
                    "receives organization_id."
                ),
                "file": (
                    "app/repositories.py"
                ),
                "line": 1,
                "evidence": [
                    (
                        "Repository lookup "
                        "contains no tenant "
                        "argument."
                    ),
                    (
                        "The affected resource "
                        "is organization-owned."
                    ),
                ],
                "impact": (
                    "Incorrect authorization "
                    "behavior."
                ),
                "recommendation": (
                    "Restore organization "
                    "scoping."
                ),
                "verification_status": (
                    "UNVERIFIED"
                ),
                "origin": (
                    "INTRODUCED_BY_PR"
                ),
                "metadata": {
                    "root_cause": (
                        "missing organization "
                        "scope"
                    )
                },
            }
        ],
    }

    write_json(
        reports
        / "findings"
        / pr_id
        / "security-review.json",
        security,
    )

    write_json(
        reports
        / "findings"
        / pr_id
        / "code-review.json",
        code,
    )

    # Execute a real invariant instead of accepting reviewer confidence as proof.
    test_dir = reports / "verification" / pr_id / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "test_sec_001.py").write_text(
        "import runpy\nfrom pathlib import Path\n\n"
        "def test_report_stays_in_requesting_organization():\n"
        "    get_report = runpy.run_path(str(Path.cwd() / 'app/repositories.py'))['get_report']\n"
        "    assert get_report(2)['organization_id'] == 100\n",
        encoding="utf-8",
    )


def test_full_review_pipeline(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    repository = (
        create_repository(
            tmp_path
        )
    )

    reports = (
        create_review_plan(
            tmp_path,
            repository,
        )
    )

    create_reviewer_findings(
        reports
    )

    result = finalize_review(
        pr_id=(
            "example-project-pr-42"
        ),
        reports_root=reports,
    )

    assert (
        result["success"]
        is True
    )

    assert (
        result["initial_findings"]
        == 2
    )

    review_path = Path(
        result["review_json"]
    )

    assert (
        review_path.exists()
    )

    review = json.loads(
        review_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        review["pr_id"]
        == "example-project-pr-42"
    )

    assert (
        len(
            review["findings"]
        )
        == 1
    )

    final_finding = (
        review["findings"][0]
    )

    assert (
        final_finding["severity"]
        == "HIGH"
    )

    assert (
        final_finding[
            "verification_status"
        ]
        == "VERIFIED"
    )

    source_reviewers = (
        final_finding
        .get(
            "metadata",
            {},
        )
        .get(
            "source_reviewers",
            [],
        )
    )

    assert (
        "security-review"
        in source_reviewers
    )

    assert (
        "code-review"
        in source_reviewers
    )


def test_full_pipeline_generates_markdown_review(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    repository = (
        create_repository(
            tmp_path
        )
    )

    reports = (
        create_review_plan(
            tmp_path,
            repository,
        )
    )

    create_reviewer_findings(
        reports
    )

    result = finalize_review(
        pr_id=(
            "example-project-pr-42"
        ),
        reports_root=reports,
    )

    markdown_path = Path(
        result["review_markdown"]
    )

    assert (
        markdown_path.exists()
    )

    content = (
        markdown_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        "# Pull Request Review"
        in content
    )

    assert (
        "Report lookup"
        in content
        or "Organization scope"
        in content
    )


def test_full_pipeline_writes_verification_results(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    repository = (
        create_repository(
            tmp_path
        )
    )

    reports = (
        create_review_plan(
            tmp_path,
            repository,
        )
    )

    create_reviewer_findings(
        reports
    )

    result = finalize_review(
        pr_id=(
            "example-project-pr-42"
        ),
        reports_root=reports,
    )

    verification_path = Path(
        result[
            "verification_results"
        ]
    )

    assert (
        verification_path.exists()
    )

    verification = json.loads(
        verification_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        verification["pr_id"]
        == "example-project-pr-42"
    )

    assert (
        len(
            verification["results"]
        )
        == 2
    )


def test_full_pipeline_generates_metrics(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    repository = (
        create_repository(
            tmp_path
        )
    )

    reports = (
        create_review_plan(
            tmp_path,
            repository,
        )
    )

    create_reviewer_findings(
        reports
    )

    finalize_review(
        pr_id=(
            "example-project-pr-42"
        ),
        reports_root=reports,
    )

    metrics_path = (
        reports
        / "metrics"
        / (
            "example-project-pr-42"
            "-finalize.json"
        )
    )

    assert (
        metrics_path.exists()
    )

    metrics = json.loads(
        metrics_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        metrics[
            "initial_findings"
        ]
        == 2
    )

    assert (
        metrics[
            "reviewers_executed"
        ]
        == 2
    )


def test_duplicate_findings_are_consolidated(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    repository = (
        create_repository(
            tmp_path
        )
    )

    reports = (
        create_review_plan(
            tmp_path,
            repository,
        )
    )

    create_reviewer_findings(
        reports
    )

    result = finalize_review(
        pr_id=(
            "example-project-pr-42"
        ),
        reports_root=reports,
    )

    review = json.loads(
        Path(
            result[
                "review_json"
            ]
        ).read_text(
            encoding="utf-8"
        )
    )

    assert (
        len(
            review["findings"]
        )
        == 1
    )


def test_pipeline_preserves_raw_reviewer_artifacts(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    repository = (
        create_repository(
            tmp_path
        )
    )

    reports = (
        create_review_plan(
            tmp_path,
            repository,
        )
    )

    create_reviewer_findings(
        reports
    )

    finalize_review(
        pr_id=(
            "example-project-pr-42"
        ),
        reports_root=reports,
    )

    security_artifact = (
        reports
        / "findings"
        / "example-project-pr-42"
        / "security-review.json"
    )

    code_artifact = (
        reports
        / "findings"
        / "example-project-pr-42"
        / "code-review.json"
    )

    assert (
        security_artifact.exists()
    )

    assert (
        code_artifact.exists()
    )


def test_existing_bob_verification_is_preserved(tmp_path):
    repository = create_repository(tmp_path)
    reports = create_review_plan(tmp_path, repository)
    create_reviewer_findings(reports)
    pr_id = "example-project-pr-42"
    existing = {"pr_id": pr_id, "results": [{
        "finding_id": "SEC-001", "method": "MANUAL_REPOSITORY_TRACE",
        "status": "REFUTED", "evidence": ["Independent trace contradicts hypothesis"],
        "metadata": {"source": "independent Bob verifier"},
    }]}
    path = reports / "verification" / pr_id / "verification-results.json"
    write_json(path, existing)
    result = finalize_review(pr_id=pr_id, reports_root=reports)
    persisted = json.loads(path.read_text())
    assert persisted["results"][0] == {**existing["results"][0],
        "command": None, "test_file": None, "expected_result": None,
        "actual_result": None, "notes": None}
    assert result["refuted_findings"] == 1
    review = json.loads(Path(result["review_json"]).read_text())
    assert all(item["id"] != "SEC-001" for item in review["findings"])


def test_finalize_rejects_invalid_reviewer_contract(tmp_path):
    import pytest

    from scripts.finalize_review import FinalizeReviewError
    repository = create_repository(tmp_path)
    reports = create_review_plan(tmp_path, repository)
    create_reviewer_findings(reports)
    path = reports / "findings/example-project-pr-42/security-review.json"
    payload = json.loads(path.read_text())
    payload["findings"][0]["severity"] = "FATAL"
    write_json(path, payload)
    with pytest.raises(FinalizeReviewError, match="Invalid artifact"):
        finalize_review(pr_id="example-project-pr-42", reports_root=reports)


def test_flask_displays_finalized_review(tmp_path):
    from app import create_app
    repository = create_repository(tmp_path)
    reports = create_review_plan(tmp_path, repository)
    create_reviewer_findings(reports)
    result = finalize_review(pr_id="example-project-pr-42", reports_root=reports)
    app = create_app({"TESTING": True, "PR_GUARDIAN_REPORTS": str(reports)})
    client = app.test_client()
    assert client.get("/").status_code == 200
    response = client.get("/reviews/example-project-pr-42")
    assert response.status_code == 200
    assert b"Report lookup" in response.data
    assert b"```" not in response.data
    assert client.get("/reviews/missing").status_code == 404
    assert client.post("/analyze", data={}).status_code == 302
    assert result["final_findings"] == 1
    metrics = json.loads((reports / "metrics/example-project-pr-42-finalize.json").read_text())
    assert metrics["generated_tests"] == 1
    assert metrics["tests_failed"] == 1
    assert metrics["analysis_duration_seconds"] > 0
