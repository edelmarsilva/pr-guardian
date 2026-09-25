from __future__ import annotations

from pathlib import Path

from flask import current_app

from github import (
    GitHubClient,
    PullRequestService,
)
from guardian import (
    DefaultFindingVerifier,
    DefaultReviewSynthesizer,
    OrchestratorConfig,
    PRGuardianOrchestrator,
)

from .reviewers import build_reviewer_registry


class ReviewServiceError(RuntimeError):
    """Raised when a PR Guardian analysis cannot be completed."""

class ReviewService:
    """
    Application service responsible for creating and executing
    the PR Guardian orchestration pipeline.

    Flask routes should interact with this service rather than with
    GitHub or guardian components directly.
    """

    def analyze(
        self,
        *,
        owner: str,
        repository: str,
        pull_number: int,
        remote_url: str | None = None,
    ):
        orchestrator = self._build_orchestrator()

        try:
            return orchestrator.analyze_pull_request(
                owner=owner,
                repository=repository,
                pull_number=pull_number,
                remote_url=remote_url,
            )
        except Exception as exc:
            raise ReviewServiceError(
                f"Unable to analyze Pull Request: {exc}"
            ) from exc

    def _build_orchestrator(
        self,
    ) -> PRGuardianOrchestrator:
        github_client = GitHubClient(
            token=current_app.config.get(
                "GITHUB_TOKEN"
            )
        )

        pull_request_service = (
            PullRequestService(
                github_client
            )
        )

        reviewers = (
            build_reviewer_registry()
        )

        verifier = (
            DefaultFindingVerifier(reports_root=current_app.config["PR_GUARDIAN_REPORTS"])
        )

        synthesizer = (
            DefaultReviewSynthesizer()
        )

        config = OrchestratorConfig(
            workspace_root=Path(
                current_app.config[
                    "PR_GUARDIAN_WORKSPACE"
                ]
            ),
            reports_root=Path(
                current_app.config[
                    "PR_GUARDIAN_REPORTS"
                ]
            ),
            run_verification=bool(
                current_app.config.get(
                    "PR_GUARDIAN_RUN_VERIFICATION",
                    True,
                )
            ),
            fail_fast=False,
        )

        return PRGuardianOrchestrator(
            pull_request_service=(
                pull_request_service
            ),
            reviewers=reviewers,
            verifier=verifier,
            synthesizer=synthesizer,
            config=config,
        )
