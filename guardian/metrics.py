from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from models import (
    Finding,
    ReviewMetrics,
    VerificationResult,
    VerificationStatus,
    )

from .orchestrator import ReviewerExecution
from .router import RoutingResult

@dataclass(slots=True)
class VerificationMetrics:
    total_results: int = 0

    verified: int = 0
    refuted: int = 0
    unverified: int = 0
    verification_failed: int = 0
    not_applicable: int = 0

    verification_rate: float = 0.0
    refutation_rate: float = 0.0

@dataclass(slots=True)
class RoutingMetrics:
    available_reviewers: int = 0
    selected_reviewers: int = 0
    skipped_reviewers: int = 0

    routing_reduction_percent: float = 0.0

@dataclass(slots=True)
class SynthesisMetrics:
    initial_findings: int = 0
    refuted_findings: int = 0
    duplicate_findings_removed: int = 0
    suppressed_findings: int = 0
    final_findings: int = 0

    finding_reduction_percent: float = 0.0

@dataclass(slots=True)
class ExecutionMetrics:
    reviewers_executed: int = 0
    reviewer_failures: int = 0

    total_reviewer_duration_seconds: float = 0.0
    average_reviewer_duration_seconds: float = 0.0

    slowest_reviewer: str | None = None
    slowest_reviewer_duration_seconds: float = 0.0

@dataclass(slots=True)
class PRGuardianMetrics:
    routing: RoutingMetrics
    verification: VerificationMetrics
    synthesis: SynthesisMetrics
    execution: ExecutionMetrics

    extra: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "routing": {
                "available_reviewers": (
                    self.routing.available_reviewers
                ),
                "selected_reviewers": (
                    self.routing.selected_reviewers
                ),
                "skipped_reviewers": (
                    self.routing.skipped_reviewers
                ),
                "routing_reduction_percent": (
                    self.routing.routing_reduction_percent
                ),
            },
            "verification": {
                "total_results": (
                    self.verification.total_results
                ),
                "verified": (
                    self.verification.verified
                ),
                "refuted": (
                    self.verification.refuted
                ),
                "unverified": (
                    self.verification.unverified
                ),
                "verification_failed": (
                    self.verification.verification_failed
                ),
                "not_applicable": (
                    self.verification.not_applicable
                ),
                "verification_rate": (
                    self.verification.verification_rate
                ),
                "refutation_rate": (
                    self.verification.refutation_rate
                ),
            },
            "synthesis": {
                "initial_findings": (
                    self.synthesis.initial_findings
                ),
                "refuted_findings": (
                    self.synthesis.refuted_findings
                ),
                "duplicate_findings_removed": (
                    self.synthesis.duplicate_findings_removed
                ),
                "suppressed_findings": (
                    self.synthesis.suppressed_findings
                ),
                "final_findings": (
                    self.synthesis.final_findings
                ),
                "finding_reduction_percent": (
                    self.synthesis.finding_reduction_percent
                ),
            },
            "execution": {
                "reviewers_executed": (
                    self.execution.reviewers_executed
                ),
                "reviewer_failures": (
                    self.execution.reviewer_failures
                ),
                "total_reviewer_duration_seconds": (
                    self.execution.total_reviewer_duration_seconds
                ),
                "average_reviewer_duration_seconds": (
                    self.execution.average_reviewer_duration_seconds
                ),
                "slowest_reviewer": (
                    self.execution.slowest_reviewer
                ),
                "slowest_reviewer_duration_seconds": (
                    self.execution.slowest_reviewer_duration_seconds
                ),
            },
            "extra": self.extra,
        }

class MetricsCalculator:
    """
    Consolidates measurable signals from the PR Guardian pipeline.

    This class intentionally avoids arbitrary quality scores.
    Metrics should remain observable and reproducible.
    """

    def calculate(
        self,
        *,
        routing: RoutingResult,
        reviewer_executions: list[ReviewerExecution],
        findings: list[Finding],
        verifications: list[VerificationResult],
        review_metrics: ReviewMetrics,
        total_available_reviewers: int,
    ) -> PRGuardianMetrics:
        return PRGuardianMetrics(
            routing=self._routing_metrics(
                routing,
                total_available_reviewers,
            ),
            verification=self._verification_metrics(
                verifications
            ),
            synthesis=self._synthesis_metrics(
                findings,
                review_metrics,
            ),
            execution=self._execution_metrics(
                reviewer_executions
            ),
            extra={
                "files_changed": (
                    review_metrics.files_changed
                ),
                "lines_added": (
                    review_metrics.lines_added
                ),
                "lines_removed": (
                    review_metrics.lines_removed
                ),
                "analysis_duration_seconds": (
                    review_metrics.analysis_duration_seconds
                ),
                "verification_duration_seconds": (
                    review_metrics.verification_duration_seconds
                ),
            },
        )

    @staticmethod
    def _routing_metrics(
        routing: RoutingResult,
        total_available_reviewers: int,
    ) -> RoutingMetrics:
        selected = len(
            routing.selected_reviewers
        )

        skipped = max(
            total_available_reviewers
            - selected,
            0,
        )

        reduction = 0.0

        if total_available_reviewers > 0:
            reduction = (
                skipped
                / total_available_reviewers
                * 100
            )

        return RoutingMetrics(
            available_reviewers=(
                total_available_reviewers
            ),
            selected_reviewers=selected,
            skipped_reviewers=skipped,
            routing_reduction_percent=round(
                reduction,
                2,
            ),
        )

    @staticmethod
    def _verification_metrics(
        verifications: list[
            VerificationResult
        ],
    ) -> VerificationMetrics:
        metrics = VerificationMetrics(
            total_results=len(
                verifications
            )
        )

        for result in verifications:
            if (
                result.status
                == VerificationStatus.VERIFIED
            ):
                metrics.verified += 1

            elif (
                result.status
                == VerificationStatus.REFUTED
            ):
                metrics.refuted += 1

            elif (
                result.status
                == VerificationStatus.UNVERIFIED
            ):
                metrics.unverified += 1

            elif (
                result.status
                == VerificationStatus.VERIFICATION_FAILED
            ):
                metrics.verification_failed += 1

            elif (
                result.status
                == VerificationStatus.NOT_APPLICABLE
            ):
                metrics.not_applicable += 1

        attempted = (
            metrics.verified
            + metrics.refuted
            + metrics.unverified
            + metrics.verification_failed
        )

        if attempted > 0:
            metrics.verification_rate = round(
                metrics.verified
                / attempted
                * 100,
                2,
            )

        concluded = (
            metrics.verified
            + metrics.refuted
        )

        if concluded > 0:
            metrics.refutation_rate = round(
                metrics.refuted
                / concluded
                * 100,
                2,
            )

        return metrics

    @staticmethod
    def _synthesis_metrics(
        findings: list[Finding],
        review_metrics: ReviewMetrics,
    ) -> SynthesisMetrics:
        initial = len(
            findings
        )

        final = (
            review_metrics.final_findings
        )

        removed = max(
            initial - final,
            0,
        )

        reduction = 0.0

        if initial > 0:
            reduction = (
                removed
                / initial
                * 100
            )

        return SynthesisMetrics(
            initial_findings=initial,
            refuted_findings=(
                review_metrics.refuted_findings
            ),
            duplicate_findings_removed=(
                review_metrics
                .duplicate_findings_removed
            ),
            suppressed_findings=(
                review_metrics.suppressed_findings
            ),
            final_findings=final,
            finding_reduction_percent=round(
                reduction,
                2,
            ),
        )

    @staticmethod
    def _execution_metrics(
        executions: list[
            ReviewerExecution
        ],
    ) -> ExecutionMetrics:
        successful = [
            execution
            for execution in executions
            if execution.success
        ]

        failures = [
            execution
            for execution in executions
            if not execution.success
        ]

        durations = [
            execution.duration_seconds
            for execution in successful
        ]

        total_duration = sum(
            durations
        )

        average_duration = (
            mean(durations)
            if durations
            else 0.0
        )

        slowest_reviewer = None
        slowest_duration = 0.0

        if successful:
            slowest = max(
                successful,
                key=lambda execution: (
                    execution.duration_seconds
                ),
            )

            slowest_reviewer = (
                slowest.reviewer
            )

            slowest_duration = (
                slowest.duration_seconds
            )

        return ExecutionMetrics(
            reviewers_executed=len(
                successful
            ),
            reviewer_failures=len(
                failures
            ),
            total_reviewer_duration_seconds=round(
                total_duration,
                4,
            ),
            average_reviewer_duration_seconds=round(
                average_duration,
                4,
            ),
            slowest_reviewer=(
                slowest_reviewer
            ),
            slowest_reviewer_duration_seconds=round(
                slowest_duration,
                4,
            ),
        )
