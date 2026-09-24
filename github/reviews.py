from **future** import annotations

from dataclasses import dataclass, field
from typing import Any

from .client import GitHubAPIError, GitHubClient

@dataclass(slots=True)
class GitHubReviewComment:
path: str
line: int
body: str
side: str = "RIGHT"

@dataclass(slots=True)
class GitHubReviewPayload:
body: str
event: str = "COMMENT"
commit_id: str | None = None
comments: list[GitHubReviewComment] = field(default_factory=list)

class GitHubReviewService:
def **init**(
self,
client: GitHubClient,
) -> None:
self.client = client

```
def create_review(
    self,
    owner: str,
    repository: str,
    pull_number: int,
    payload: GitHubReviewPayload,
) -> dict[str, Any]:
    """
    Publish a Pull Request review.

    This method must only be called after an explicit publication
    decision has been made by the orchestration layer.
    """

    data: dict[str, Any] = {
        "body": payload.body,
        "event": payload.event,
    }

    if payload.commit_id:
        data["commit_id"] = payload.commit_id

    if payload.comments:
        data["comments"] = [
            {
                "path": comment.path,
                "line": comment.line,
                "side": comment.side,
                "body": comment.body,
            }
            for comment in payload.comments
        ]

    response = self.client.post(
        (
            f"/repos/{owner}/{repository}"
            f"/pulls/{pull_number}/reviews"
        ),
        json=data,
    )

    if not isinstance(response.data, dict):
        raise GitHubAPIError(
            "Unexpected GitHub review response."
        )

    return response.data

def create_summary_comment(
    self,
    owner: str,
    repository: str,
    pull_number: int,
    *,
    body: str,
) -> dict[str, Any]:
    """
    Create a review containing only the summary body.
    """

    payload = GitHubReviewPayload(
        body=body,
        event="COMMENT",
    )

    return self.create_review(
        owner,
        repository,
        pull_number,
        payload,
    )

def create_request_changes_review(
    self,
    owner: str,
    repository: str,
    pull_number: int,
    *,
    body: str,
    comments: list[GitHubReviewComment] | None = None,
    commit_id: str | None = None,
) -> dict[str, Any]:
    """
    Publish a REQUEST_CHANGES review.

    The caller is responsible for deciding whether this action is
    appropriate.
    """

    payload = GitHubReviewPayload(
        body=body,
        event="REQUEST_CHANGES",
        commit_id=commit_id,
        comments=comments or [],
    )

    return self.create_review(
        owner,
        repository,
        pull_number,
        payload,
    )
```