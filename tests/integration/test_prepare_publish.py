from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from github import GitHubClient, PullRequestService
from models import ChangedFile, PullRequest
from scripts import prepare_review as prepare
from scripts.publish_review import PublishReviewError, publish_review


@pytest.fixture
def remote(monkeypatch):
    pr = PullRequest(
        repository_owner="example", repository_name="project", number=42,
        title="Update service", description="Synthetic fixture", base_branch="main",
        head_branch="feature", base_sha="base123", head_sha="head456",
        changed_files=[ChangedFile(filename="app/service.py", status="modified",
                                   patch="@@ -1 +1 @@\n-old\n+new")],
    )
    monkeypatch.setenv("GITHUB_TOKEN", "synthetic-token")
    monkeypatch.setattr(PullRequestService, "get_pull_request", lambda self, **kwargs: pr)
    def reject_network(*args, **kwargs):
        pytest.fail("No GitHub request may occur in this controlled test")
    monkeypatch.setattr(GitHubClient, "_request", reject_network)
    return pr


def test_prepare_builds_context_and_custom_report_paths(tmp_path, monkeypatch, remote):
    def clone(**kwargs):
        destination = kwargs["destination"]
        (destination / "app").mkdir(parents=True)
        (destination / "app/service.py").write_text("def get():\n    return 1\n")
        (destination / "app/routes.py").write_text("from app.service import get\n")
        return SimpleNamespace(path=destination)
    monkeypatch.setattr(prepare, "prepare_pull_request_workspace", clone)
    reports = tmp_path / "custom-reports"
    plan = prepare.prepare_review("example/project#42", workspace_root=tmp_path / "repositories",
                                  reports_root=reports)
    assert plan["potentially_affected_files"] == ["app/routes.py"]
    assert "code-review" in plan["selected_reviewers"]
    assert "queue-review" not in plan["selected_reviewers"]
    for key in ("context_path", "routing_path"):
        assert Path(plan[key]).is_file()
    assert json.loads(Path(plan["context_path"]).read_text())["head_sha"] == remote.head_sha
    assert all(task["output"].startswith(str(reports)) for task in plan["reviewer_tasks"])


def write_review(tmp_path, remote, **updates):
    payload = {"pr_id": remote.identifier, "summary": "Controlled review", "findings": [],
               "metadata": {"head_sha": remote.head_sha}}
    payload.update(updates)
    path = tmp_path / "review.json"
    path.write_text(json.dumps(payload))
    return path


def test_publish_dry_run_does_not_write(tmp_path, remote):
    path = write_review(tmp_path, remote)
    before = path.read_bytes()
    result = publish_review(repository="example/project", pull_number=42,
                            review_path=path, event="COMMENT", dry_run=True)
    assert result["dry_run"] is True
    assert result["payload"]["commit_id"] == remote.head_sha
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("dry_run", [True, False])
@pytest.mark.parametrize("metadata", [{}, {"head_sha": "old-head"}])
def test_publish_rejects_unbound_or_stale_review(tmp_path, remote, metadata, dry_run):
    path = write_review(tmp_path, remote, metadata=metadata)
    with pytest.raises(PublishReviewError, match="missing or stale"):
        publish_review(repository="example/project", pull_number=42,
                       review_path=path, event="COMMENT", dry_run=dry_run)


def test_publish_rejects_different_pr(tmp_path, remote):
    path = write_review(tmp_path, remote, pr_id="example-other-pr-42")
    with pytest.raises(PublishReviewError, match="different Pull Request"):
        publish_review(repository="example/project", pull_number=42,
                       review_path=path, event="COMMENT", dry_run=True)
