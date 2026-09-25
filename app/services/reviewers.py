from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from guardian import (
    PullRequestContext,
    ReviewDomain,
    )
from models import Finding, PullRequest

class BobReviewerBackend(Protocol):
    """
    Adapter contract for invoking an IBM Bob reviewer.

    The concrete Bob integration can later use the mechanism provided by
    the hackathon environment without changing the orchestrator.
    """

    def execute(
        self,
        *,
        reviewer: str,
        pull_request: PullRequest,
        context: PullRequestContext,
        repository_path: Path,
    ) -> list[Finding]:
        ...

@dataclass(slots=True)
class BobSkillReviewer:
    name: str
    backend: BobReviewerBackend

    def review(
        self,
        *,
        pull_request: PullRequest,
        context: PullRequestContext,
        repository_path: Path,
    ) -> list[Finding]:
        findings = self.backend.execute(
            reviewer=self.name,
            pull_request=pull_request,
            context=context,
            repository_path=repository_path,
        )

        for finding in findings:
            if finding.reviewer is None:
                finding.reviewer = (
                    self.name
                )

        return findings

class PlaceholderBobBackend:
    """
    Temporary backend used while the Bob execution adapter is not yet
    connected.

    It intentionally returns no findings rather than fabricating them.
    """

    def execute(
        self,
        *,
        reviewer: str,
        pull_request: PullRequest,
        context: PullRequestContext,
        repository_path: Path,
    ) -> list[Finding]:
        return []

def build_reviewer_registry(
    backend: BobReviewerBackend | None = None,
) -> dict[
    ReviewDomain,
    BobSkillReviewer,
]:
    backend = (
        backend
        or PlaceholderBobBackend()
    )

    return {
        ReviewDomain.CODE: (
            BobSkillReviewer(
                name="code-review",
                backend=backend,
            )
        ),
        ReviewDomain.SECURITY: (
            BobSkillReviewer(
                name="security-review",
                backend=backend,
            )
        ),
        ReviewDomain.TEST: (
            BobSkillReviewer(
                name="test-impact",
                backend=backend,
            )
        ),
        ReviewDomain.ARCHITECTURE: (
            BobSkillReviewer(
                name="architecture-review",
                backend=backend,
            )
        ),
        ReviewDomain.DATABASE: (
            BobSkillReviewer(
                name="database-review",
                backend=backend,
            )
        ),
        ReviewDomain.API: (
            BobSkillReviewer(
                name="api-review",
                backend=backend,
            )
        ),
        ReviewDomain.QUEUE: (
            BobSkillReviewer(
                name="queue-review",
                backend=backend,
            )
        ),
    }
