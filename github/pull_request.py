from **future** import annotations

from typing import Any

from models import ChangedFile, PullRequest

from .client import GitHubAPIError, GitHubClient
from .models import (
GitHubChangedFile,
GitHubCommit,
GitHubPullRequestData,
)

class PullRequestService:
def **init**(
self,
client: GitHubClient,
) -> None:
self.client = client

```
def get_pull_request(
    self,
    owner: str,
    repository: str,
    number: int,
) -> PullRequest:
    """
    Retrieve a complete Pull Request context from GitHub.

    Includes:
    - metadata
    - changed files
    - commits
    """

    raw_pr = self._fetch_pull_request(
        owner,
        repository,
        number,
    )

    files = self._fetch_files(
        owner,
        repository,
        number,
    )

    commits = self._fetch_commits(
        owner,
        repository,
        number,
    )

    return PullRequest(
        repository_owner=owner,
        repository_name=repository,
        number=raw_pr.number,
        title=raw_pr.title,
        description=raw_pr.body,
        base_branch=raw_pr.base_branch,
        head_branch=raw_pr.head_branch,
        base_sha=raw_pr.base_sha,
        head_sha=raw_pr.head_sha,
        author=raw_pr.author,
        additions=raw_pr.additions,
        deletions=raw_pr.deletions,
        changed_files_count=raw_pr.changed_files,
        commit_count=raw_pr.commits,
        changed_files=[
            ChangedFile(
                filename=file.filename,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                patch=file.patch,
                previous_filename=file.previous_filename,
            )
            for file in files
        ],
        commits=[
            commit.message
            for commit in commits
        ],
        html_url=raw_pr.html_url,
        metadata={
            "commit_shas": [
                commit.sha
                for commit in commits
            ],
        },
    )

def _fetch_pull_request(
    self,
    owner: str,
    repository: str,
    number: int,
) -> GitHubPullRequestData:
    response = self.client.get(
        f"/repos/{owner}/{repository}/pulls/{number}"
    )

    data = response.data

    if not isinstance(data, dict):
        raise GitHubAPIError(
            "Unexpected Pull Request response."
        )

    return self._parse_pull_request(data)

def _fetch_files(
    self,
    owner: str,
    repository: str,
    number: int,
) -> list[GitHubChangedFile]:
    raw_files = self.client.paginate(
        f"/repos/{owner}/{repository}/pulls/{number}/files"
    )

    files: list[GitHubChangedFile] = []

    for item in raw_files:
        if not isinstance(item, dict):
            continue

        files.append(
            GitHubChangedFile(
                filename=item["filename"],
                status=item["status"],
                additions=item.get("additions", 0),
                deletions=item.get("deletions", 0),
                changes=item.get("changes", 0),
                patch=item.get("patch"),
                previous_filename=item.get(
                    "previous_filename"
                ),
            )
        )

    return files

def _fetch_commits(
    self,
    owner: str,
    repository: str,
    number: int,
) -> list[GitHubCommit]:
    raw_commits = self.client.paginate(
        f"/repos/{owner}/{repository}/pulls/{number}/commits"
    )

    commits: list[GitHubCommit] = []

    for item in raw_commits:
        if not isinstance(item, dict):
            continue

        commit_data = item.get(
            "commit",
            {},
        )

        author_data = commit_data.get(
            "author",
            {},
        )

        commits.append(
            GitHubCommit(
                sha=item["sha"],
                message=commit_data.get(
                    "message",
                    "",
                ),
                author=author_data.get(
                    "name"
                ),
            )
        )

    return commits

@staticmethod
def _parse_pull_request(
    data: dict[str, Any],
) -> GitHubPullRequestData:
    user = data.get("user") or {}

    base = data.get("base") or {}
    head = data.get("head") or {}

    return GitHubPullRequestData(
        number=data["number"],
        title=data.get("title", ""),
        body=data.get("body"),
        author=user.get("login"),
        base_branch=base.get("ref", ""),
        head_branch=head.get("ref", ""),
        base_sha=base.get("sha", ""),
        head_sha=head.get("sha", ""),
        additions=data.get(
            "additions",
            0,
        ),
        deletions=data.get(
            "deletions",
            0,
        ),
        changed_files=data.get(
            "changed_files",
            0,
        ),
        commits=data.get(
            "commits",
            0,
        ),
        html_url=data.get(
            "html_url"
        ),
    )
```