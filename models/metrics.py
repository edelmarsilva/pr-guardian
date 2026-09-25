from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReviewMetrics:
    files_changed: int = 0
    files_analyzed: int = 0

    lines_added: int = 0
    lines_removed: int = 0

    reviewers_selected: int = 0
    reviewers_executed: int = 0

    initial_findings: int = 0

    verified_findings: int = 0
    refuted_findings: int = 0
    unverified_findings: int = 0

    duplicate_findings_removed: int = 0
    suppressed_findings: int = 0

    final_findings: int = 0

    blocking_findings: int = 0
    non_blocking_findings: int = 0
    advisory_findings: int = 0

    tests_executed: int = 0
    tests_passed: int = 0
    tests_failed: int = 0

    generated_tests: int = 0

    analysis_duration_seconds: float = 0.0
    verification_duration_seconds: float = 0.0

    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_changed": self.files_changed,
            "files_analyzed": self.files_analyzed,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "reviewers_selected": self.reviewers_selected,
            "reviewers_executed": self.reviewers_executed,
            "initial_findings": self.initial_findings,
            "verified_findings": self.verified_findings,
            "refuted_findings": self.refuted_findings,
            "unverified_findings": self.unverified_findings,
            "duplicate_findings_removed": self.duplicate_findings_removed,
            "suppressed_findings": self.suppressed_findings,
            "final_findings": self.final_findings,
            "blocking_findings": self.blocking_findings,
            "non_blocking_findings": self.non_blocking_findings,
            "advisory_findings": self.advisory_findings,
            "tests_executed": self.tests_executed,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "generated_tests": self.generated_tests,
            "analysis_duration_seconds": self.analysis_duration_seconds,
            "verification_duration_seconds": self.verification_duration_seconds,
            "extra": self.extra,
        }
