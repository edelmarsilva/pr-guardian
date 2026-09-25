from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from github import PullRequestService
from models import (
    Finding,
    PullRequest,
    Review,
    ReviewMetrics,
    VerificationResult,
    )
from repository import prepare_pull_request_workspace

from .context_builder import (
    ContextBuilder,
    PullRequestContext,
    )
from .router import (
    ReviewDomain,
    ReviewerRouter,
    RoutingResult,
    )

class Reviewer(Protocol):
    """
    Contract implemented by specialized reviewers.

    The orchestrator does not need to know whether the reviewer is
    implemented by IBM Bob, a deterministic analyzer, or another adapter.
    """

    name: str

    def review(
        self,
        *,
        pull_request: PullRequest,
        context: PullRequestContext,
        repository_path: Path,
    ) -> list[Finding]:
        ...

class FindingVerifier(Protocol):
    def verify(
        self,
        *,
        pull_request: PullRequest,
        context: PullRequestContext,
        repository_path: Path,
        findings: list[Finding],
    ) -> list[VerificationResult]:
        ...

class ReviewSynthesizer(Protocol):
    def synthesize(
        self,
        *,
        pull_request: PullRequest,
        context: PullRequestContext,
        findings: list[Finding],
        verifications: list[VerificationResult],
        reviewers_executed: list[str],
        metrics: ReviewMetrics,
    ) -> Review:
        ...

@dataclass(slots=True)
class OrchestratorConfig:
    workspace_root: Path = Path(
    "workspace/repositories"
    )

    reports_root: Path = Path(
        "reports"
    )

    preserve_workspace: bool = True

    run_verification: bool = True

    fail_fast: bool = False

@dataclass(slots=True)
class ReviewerExecution:
    reviewer: str

    success: bool

    findings: list[Finding] = field(
        default_factory=list
    )

    duration_seconds: float = 0.0

    error: str | None = None

@dataclass(slots=True)
class AnalysisResult:
    pull_request: PullRequest
    context: PullRequestContext

    routing: RoutingResult

    reviewer_executions: list[
        ReviewerExecution
    ]

    findings: list[Finding]

    verifications: list[
        VerificationResult
    ]

    review: Review

    metrics: ReviewMetrics

    workspace_path: Path

class PRGuardianOrchestrator:
    """
    Coordinates the complete PR Guardian analysis pipeline.

    Responsibilities:

    GitHub ingestion
        ↓
    repository workspace
        ↓
    context building
        ↓
    adaptive routing
        ↓
    specialized review
        ↓
    verification
        ↓
    synthesis
        ↓
    persisted artifacts
    """

    def __init__(
        self,
        *,
        pull_request_service: PullRequestService,
        reviewers: dict[
            ReviewDomain,
            Reviewer,
        ],
        verifier: FindingVerifier,
        synthesizer: ReviewSynthesizer,
        context_builder: ContextBuilder | None = None,
        router: ReviewerRouter | None = None,
        config: OrchestratorConfig | None = None,
    ) -> None:
        self.pull_request_service = (
            pull_request_service
        )

        self.reviewers = reviewers

        self.verifier = verifier
        self.synthesizer = synthesizer

        self.context_builder = (
            context_builder
            or ContextBuilder()
        )

        self.router = (
            router
            or ReviewerRouter()
        )

        self.config = (
            config
            or OrchestratorConfig()
        )

    def analyze_pull_request(
        self,
        *,
        owner: str,
        repository: str,
        pull_number: int,
        remote_url: str | None = None,
    ) -> AnalysisResult:
        started = time.perf_counter()

        pull_request = (
            self.pull_request_service
            .get_pull_request(
                owner=owner,
                repository=repository,
                number=pull_number,
            )
        )

        if remote_url is None:
            remote_url = (
                f"https://github.com/"
                f"{owner}/{repository}.git"
            )

        workspace_path = (
            self._workspace_path(
                pull_request
            )
        )

        workspace = (
            prepare_pull_request_workspace(
                remote_url=remote_url,
                destination=workspace_path,
                base_sha=pull_request.base_sha,
                head_sha=pull_request.head_sha,
            )
        )

        context = self.context_builder.build(
            pull_request,
            workspace.path,
        )

        self._persist_context(
            pull_request,
            context,
        )

        routing = self.router.route(
            pull_request
        )

        self._persist_routing(
            pull_request,
            routing,
        )

        executions = (
            self._execute_reviewers(
                pull_request=pull_request,
                context=context,
                repository_path=workspace.path,
                routing=routing,
            )
        )

        findings = [
            finding
            for execution in executions
            for finding in execution.findings
        ]

        self._persist_findings(
            pull_request,
            findings,
        )

        verification_started = (
            time.perf_counter()
        )

        if (
            self.config.run_verification
            and findings
        ):
            verifications = (
                self.verifier.verify(
                    pull_request=pull_request,
                    context=context,
                    repository_path=workspace.path,
                    findings=findings,
                )
            )
        else:
            verifications = []

        verification_duration = (
            time.perf_counter()
            - verification_started
        )

        self._persist_verifications(
            pull_request,
            verifications,
        )

        metrics = self._build_metrics(
            pull_request=pull_request,
            executions=executions,
            findings=findings,
            verifications=verifications,
            verification_duration=(
                verification_duration
            ),
        )

        review = (
            self.synthesizer.synthesize(
                pull_request=pull_request,
                context=context,
                findings=findings,
                verifications=verifications,
                reviewers_executed=[
                    execution.reviewer
                    for execution in executions
                    if execution.success
                ],
                metrics=metrics,
            )
        )

        metrics.analysis_duration_seconds = (
            time.perf_counter()
            - started
        )

        self._persist_review(
            pull_request,
            review,
        )

        self._persist_metrics(
            pull_request,
            metrics,
        )

        return AnalysisResult(
            pull_request=pull_request,
            context=context,
            routing=routing,
            reviewer_executions=executions,
            findings=findings,
            verifications=verifications,
            review=review,
            metrics=metrics,
            workspace_path=workspace.path,
        )

    def _execute_reviewers(
        self,
        *,
        pull_request: PullRequest,
        context: PullRequestContext,
        repository_path: Path,
        routing: RoutingResult,
    ) -> list[ReviewerExecution]:
        executions: list[
            ReviewerExecution
        ] = []

        for domain in (
            routing.selected_reviewers
        ):
            reviewer = self.reviewers.get(
                domain
            )

            if reviewer is None:
                executions.append(
                    ReviewerExecution(
                        reviewer=domain.value,
                        success=False,
                        error=(
                            "No reviewer implementation "
                            "registered."
                        ),
                    )
                )

                if self.config.fail_fast:
                    raise RuntimeError(
                        f"Missing reviewer: "
                        f"{domain.value}"
                    )

                continue

            started = time.perf_counter()

            try:
                findings = reviewer.review(
                    pull_request=pull_request,
                    context=context,
                    repository_path=(
                        repository_path
                    ),
                )
            except Exception as exc:
                execution = ReviewerExecution(
                    reviewer=domain.value,
                    success=False,
                    duration_seconds=(
                        time.perf_counter()
                        - started
                    ),
                    error=str(exc),
                )

                executions.append(
                    execution
                )

                if self.config.fail_fast:
                    raise

                continue

            executions.append(
                ReviewerExecution(
                    reviewer=domain.value,
                    success=True,
                    findings=findings,
                    duration_seconds=(
                        time.perf_counter()
                        - started
                    ),
                )
            )

        return executions

    def _build_metrics(
        self,
        *,
        pull_request: PullRequest,
        executions: list[
            ReviewerExecution
        ],
        findings: list[Finding],
        verifications: list[
            VerificationResult
        ],
        verification_duration: float,
    ) -> ReviewMetrics:
        metrics = ReviewMetrics(
            files_changed=(
                pull_request.changed_files_count
                or len(
                    pull_request.changed_files
                )
            ),
            files_analyzed=len(
                pull_request.changed_files
            ),
            lines_added=pull_request.additions,
            lines_removed=(
                pull_request.deletions
            ),
            reviewers_selected=len(
                executions
            ),
            reviewers_executed=sum(
                1
                for execution in executions
                if execution.success
            ),
            initial_findings=len(
                findings
            ),
            verification_duration_seconds=(
                verification_duration
            ),
        )

        for verification in verifications:
            status = (
                verification.status.value
            )

            if status == "VERIFIED":
                metrics.verified_findings += 1

            elif status == "REFUTED":
                metrics.refuted_findings += 1

            elif status == "UNVERIFIED":
                metrics.unverified_findings += 1

        metrics.extra[
            "reviewer_failures"
        ] = [
            {
                "reviewer": execution.reviewer,
                "error": execution.error,
            }
            for execution in executions
            if not execution.success
        ]

        metrics.extra[
            "reviewer_durations"
        ] = {
            execution.reviewer: (
                execution.duration_seconds
            )
            for execution in executions
        }

        return metrics

    def _workspace_path(
        self,
        pull_request: PullRequest,
    ) -> Path:
        return (
            self.config.workspace_root
            / pull_request.identifier
        )

    def _raw_directory(
        self,
        pull_request: PullRequest,
    ) -> Path:
        return (
            self.config.reports_root
            / "raw"
            / pull_request.identifier
        )

    def _findings_directory(
        self,
        pull_request: PullRequest,
    ) -> Path:
        return (
            self.config.reports_root
            / "findings"
            / pull_request.identifier
        )

    def _verification_directory(
        self,
        pull_request: PullRequest,
    ) -> Path:
        return (
            self.config.reports_root
            / "verification"
            / pull_request.identifier
        )

    def _review_directory(
        self,
        pull_request: PullRequest,
    ) -> Path:
        return (
            self.config.reports_root
            / "reviews"
            / pull_request.identifier
        )

    def _metrics_directory(
        self,
    ) -> Path:
        return (
            self.config.reports_root
            / "metrics"
        )

    def _persist_context(
        self,
        pull_request: PullRequest,
        context: PullRequestContext,
    ) -> None:
        path = (
            self._raw_directory(
                pull_request
            )
            / "pr-context.json"
        )

        self._write_json(
            path,
            context.to_dict(),
        )

    def _persist_routing(
        self,
        pull_request: PullRequest,
        routing: RoutingResult,
    ) -> None:
        payload = {
            "selected_reviewers": [
                reviewer.value
                for reviewer in (
                    routing.selected_reviewers
                )
            ],
            "decisions": [
                {
                    "reviewer": (
                        decision.reviewer.value
                    ),
                    "selected": (
                        decision.selected
                    ),
                    "reasons": (
                        decision.reasons
                    ),
                    "matched_files": (
                        decision.matched_files
                    ),
                    "matched_signals": (
                        decision.matched_signals
                    ),
                }
                for decision
                in routing.decisions
            ],
        }

        self._write_json(
            (
                self._raw_directory(
                    pull_request
                )
                / "routing.json"
            ),
            payload,
        )

    def _persist_findings(
        self,
        pull_request: PullRequest,
        findings: list[Finding],
    ) -> None:
        grouped: dict[
            str,
            list[Finding],
        ] = {}

        for finding in findings:
            reviewer = (
                finding.reviewer
                or "unknown-reviewer"
            )

            grouped.setdefault(
                reviewer,
                [],
            ).append(
                finding
            )

        directory = (
            self._findings_directory(
                pull_request
            )
        )

        for reviewer, items in (
            grouped.items()
        ):
            self._write_json(
                directory
                / f"{reviewer}.json",
                {
                    "reviewer": reviewer,
                    "findings": [
                        finding.to_dict()
                        for finding in items
                    ],
                },
            )

    def _persist_verifications(
        self,
        pull_request: PullRequest,
        verifications: list[
            VerificationResult
        ],
    ) -> None:
        path = (
            self._verification_directory(
                pull_request
            )
            / "verification-results.json"
        )

        payload = {
            "pr_id": (
                pull_request.identifier
            ),
            "results": [
                verification.to_dict()
                for verification
                in verifications
            ],
        }

        self._write_json(
            path,
            payload,
        )

    def _persist_review(
        self,
        pull_request: PullRequest,
        review: Review,
    ) -> None:
        directory = (
            self._review_directory(
                pull_request
            )
        )

        self._write_json(
            directory
            / "review.json",
            review.to_dict(),
        )

        markdown = self._review_to_markdown(
            review
        )

        self._write_text(
            directory
            / "review.md",
            markdown,
        )

    def _persist_metrics(
        self,
        pull_request: PullRequest,
        metrics: ReviewMetrics,
    ) -> None:
        self._write_json(
            (
                self._metrics_directory()
                / (
                    f"{pull_request.identifier}"
                    "-orchestrator.json"
                )
            ),
            metrics.to_dict(),
        )

    @staticmethod
    def _review_to_markdown(
        review: Review,
    ) -> str:
        lines = [
            "# Pull Request Review",
            "",
            "## Summary",
            "",
            review.summary,
        ]

        findings = (
            review.publishable_findings()
        )

        if findings:
            lines.extend(
                [
                    "",
                    "## Findings",
                ]
            )

        for finding in findings:
            lines.extend(
                [
                    "",
                    (
                        f"### "
                        f"{finding.severity.value} · "
                        f"{finding.confidence.value} · "
                        f"{finding.verification_status.value}"
                        f" — {finding.title}"
                    ),
                    "",
                ]
            )

            if finding.file:
                location = finding.file

                if finding.line:
                    location += (
                        f":{finding.line}"
                    )

                lines.extend(
                    [
                        f"`{location}`",
                        "",
                    ]
                )

            lines.append(
                finding.description
            )

            if finding.impact:
                lines.extend(
                    [
                        "",
                        (
                            "**Impact:** "
                            f"{finding.impact}"
                        ),
                    ]
                )

            if finding.recommendation:
                lines.extend(
                    [
                        "",
                        (
                            "**Recommendation:** "
                            f"{finding.recommendation}"
                        ),
                    ]
                )

        return "\n".join(
            lines
        )

    @staticmethod
    def _write_json(
        path: Path,
        payload: dict[str, Any],
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _write_text(
        path: Path,
        content: str,
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            content,
            encoding="utf-8",
        )
