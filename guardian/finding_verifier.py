# guardian/finding_verifier.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analyzers.tests.pytest_runner import (
    PytestExecutionResult,
    PytestRunner,
)
from models import (
    Finding,
    PullRequest,
    VerificationMethod,
    VerificationResult,
    VerificationStatus,
)


@dataclass(slots=True)
class VerificationPolicy:
    verify_high_severity: bool = True
    verify_medium_severity: bool = True
    allow_generated_tests: bool = True
    allow_direct_code_evidence: bool = True


class DefaultFindingVerifier:
    def __init__(
        self,
        *,
        policy: VerificationPolicy | None = None,
        reports_root: Path | str = "reports",
    ) -> None:
        self.policy = (
            policy
            or VerificationPolicy()
        )

        self.reports_root = Path(
            reports_root
        )

    def verify(
        self,
        *,
        pull_request: PullRequest,
        context,
        repository_path: Path,
        findings: list[Finding],
    ) -> list[VerificationResult]:
        results: list[
            VerificationResult
        ] = []

        for finding in findings:
            result = (
                self._verify_finding(
                    pull_request=(
                        pull_request
                    ),
                    context=context,
                    repository_path=(
                        repository_path
                    ),
                    finding=finding,
                )
            )

            results.append(
                result
            )

        return results

    def _verify_finding(
        self,
        *,
        pull_request: PullRequest,
        context,
        repository_path: Path,
        finding: Finding,
    ) -> VerificationResult:
        generated_test = (
            self._find_verification_test(
                pull_request=pull_request,
                finding=finding,
            )
        )

        if (
            generated_test
            and self.policy.allow_generated_tests
        ):
            return (
                self._verify_with_generated_test(
                    repository_path=(
                        repository_path
                    ),
                    finding=finding,
                    test_file=(
                        generated_test
                    ),
                )
            )

        # Reviewer claims are not independent repository verification.

        return VerificationResult(
            finding_id=finding.id,
            method=(
                VerificationMethod
                .MANUAL_REPOSITORY_TRACE
            ),
            status=(
                VerificationStatus
                .UNVERIFIED
            ),
            evidence=list(
                finding.evidence
            ),
            notes=(
                "No deterministic "
                "verification strategy "
                "completed."
            ),
        )

    @staticmethod
    def _command_text(
        execution: PytestExecutionResult,
    ) -> str:
        """Convert analyzer_result.command list to a readable string."""
        command = execution.analyzer_result.command
        if isinstance(command, list):
            return " ".join(command)
        return str(command)

    def _verify_with_generated_test(
        self,
        *,
        repository_path: Path,
        finding: Finding,
        test_file: Path,
    ) -> VerificationResult:
        runner = PytestRunner()

        execution = runner.run(
            repository_path=(
                repository_path
            ),
            targets=[str(test_file.resolve())],
        )

        classification = (
            self._classify_test_execution(
                execution
            )
        )

        if (
            classification
            == "PRODUCT_DEFECT_REPRODUCED"
        ):
            return VerificationResult(
                finding_id=(
                    finding.id
                ),
                method=(
                    VerificationMethod
                    .GENERATED_REGRESSION_TEST
                ),
                status=(
                    VerificationStatus
                    .VERIFIED
                ),
                evidence=[
                    (
                        "Generated regression "
                        "test failed because "
                        "actual product behavior "
                        "did not satisfy the "
                        "expected invariant."
                    )
                ],
                command=(
                    self._command_text(
                        execution
                    )
                ),
                test_file=str(
                    test_file
                ),
                expected_result=(
                    "Regression test passes."
                ),
                actual_result=(
                    "Regression assertion "
                    "failed."
                ),
                notes=(
                    "The defect was reproduced "
                    "deterministically."
                ),
                metadata={
                    **self._execution_metadata(execution),
                    "failure_class": (
                        "PRODUCT_DEFECT"
                    ),
                    "exit_code": (
                        execution
                        .analyzer_result
                        .exit_code
                    ),
                },
            )

        if (
            classification
            == "EXPECTED_BEHAVIOR_CONFIRMED"
        ):
            return VerificationResult(
                finding_id=(
                    finding.id
                ),
                method=(
                    VerificationMethod
                    .GENERATED_REGRESSION_TEST
                ),
                status=(
                    VerificationStatus
                    .REFUTED
                ),
                evidence=[
                    (
                        "Generated regression "
                        "test passed against "
                        "the reviewed code."
                    )
                ],
                command=(
                    self._command_text(
                        execution
                    )
                ),
                test_file=str(
                    test_file
                ),
                expected_result=(
                    "Regression test passes."
                ),
                actual_result=(
                    "Regression test passed."
                ),
                notes=(
                    "The suspected defect "
                    "could not be reproduced."
                ),
                metadata={
                    **self._execution_metadata(execution),
                    "failure_class": None,
                    "exit_code": (
                        execution
                        .analyzer_result
                        .exit_code
                    ),
                },
            )

        return VerificationResult(
            finding_id=finding.id,
            method=(
                VerificationMethod
                .GENERATED_REGRESSION_TEST
            ),
            status=(
                VerificationStatus
                .VERIFICATION_FAILED
            ),
            evidence=[
                (
                    "Verification test could "
                    "not provide reliable "
                    "product evidence."
                )
            ],
            command=(
                self._command_text(
                    execution
                )
            ),
            test_file=str(
                test_file
            ),
            expected_result=(
                "A deterministic product "
                "behavior result."
            ),
            actual_result=(
                classification
            ),
            notes=(
                self._verification_failure_note(
                    execution,
                    classification,
                )
            ),
            metadata={
                **self._execution_metadata(execution),
                "failure_class": (
                    classification
                ),
                "exit_code": (
                    execution
                    .analyzer_result
                    .exit_code
                ),
                "stdout": (
                    execution
                    .analyzer_result
                    .stdout
                ),
                "stderr": (
                    execution
                    .analyzer_result
                    .stderr
                ),
            },
        )

    @staticmethod
    def _execution_metadata(execution: PytestExecutionResult) -> dict:
        return {
            "test_summary": {
                key: getattr(execution.summary, key)
                for key in ("passed", "failed", "errors", "skipped", "xfailed", "xpassed")
            },
            "duration_seconds": execution.analyzer_result.duration_seconds,
            "test_failures": [
                {"nodeid": test.nodeid, "phase": test.failure_phase, "message": test.message}
                for test in execution.summary.tests if test.failure_phase
            ],
            "raw_output_path": str(execution.analyzer_result.raw_output_path or ""),
        }

    def _classify_test_execution(
        self,
        execution: PytestExecutionResult,
    ) -> str:
        """
        Distinguish a real assertion mismatch from failures
        that do not prove a product defect.
        """

        from analyzers.base import AnalyzerStatus

        result = execution.analyzer_result
        summary = execution.summary
        if result.status not in {AnalyzerStatus.SUCCESS, AnalyzerStatus.FINDINGS}:
            return "ENVIRONMENT_OR_TEST_FAILURE"
        if result.exit_code not in {0, 1} or summary.errors:
            return "ENVIRONMENT_OR_TEST_FAILURE"
        if not summary.tests:
            return "UNKNOWN_TEST_FAILURE"
        if any(test.failure_phase in {"setup", "teardown"} for test in summary.tests):
            return "ENVIRONMENT_OR_TEST_FAILURE"
        if result.exit_code == 0:
            if (
                summary.passed > 0
                and sum(test.call_outcome == "passed" and test.outcome == "passed"
                        for test in summary.tests) == summary.passed
                and summary.failed == 0
                and all(
                test.outcome in {"passed", "skipped", "xfailed"}
                for test in summary.tests
                )
            ):
                return "EXPECTED_BEHAVIOR_CONFIRMED"
            return "UNKNOWN_TEST_FAILURE"

        failures = [test for test in summary.tests if test.outcome == "failed"]
        if summary.failed > 0 and len(failures) == summary.failed and all(
            test.failure_phase == "call" and test.assertion_failure
            for test in failures
        ):
            return "PRODUCT_DEFECT_REPRODUCED"
        return "ENVIRONMENT_OR_TEST_FAILURE"

    def _verification_failure_note(
        self,
        execution: PytestExecutionResult,
        classification: str,
    ) -> str:
        if (
            classification
            == "ENVIRONMENT_OR_TEST_FAILURE"
        ):
            return (
                "The verification execution "
                "failed due to test, import, "
                "fixture, dependency, or "
                "environment problems. This "
                "does not confirm the finding."
            )

        return (
            "The verification execution "
            "failed, but the failure could "
            "not be classified as a product "
            "behavior mismatch."
        )

    def _find_verification_test(
        self,
        *,
        pull_request: PullRequest,
        finding: Finding,
    ) -> Path | None:
        tests_directory = (
            self.reports_root
            / "verification"
            / pull_request.identifier
            / "tests"
        )

        if not tests_directory.exists():
            return None

        normalized_id = (
            finding.id
            .lower()
            .replace("-", "_")
        )

        candidates = sorted(
            tests_directory.glob(
                "test_*.py"
            )
        )

        for candidate in candidates:
            if (
                normalized_id
                in candidate.stem.lower()
            ):
                return candidate.resolve()

        return None
