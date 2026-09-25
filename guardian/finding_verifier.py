# guardian/finding_verifier.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analyzers.tests.pytest_runner import (
    PytestExecutionResult,
    PytestRunner,
)
from models import (
    Confidence,
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

        if (
            self.policy
            .allow_direct_code_evidence
            and finding.confidence
            == Confidence.CONFIRMED
            and len(
                finding.evidence
            )
            >= 2
        ):
            return VerificationResult(
                finding_id=(
                    finding.id
                ),
                method=(
                    VerificationMethod
                    .DIRECT_CODE_EVIDENCE
                ),
                status=(
                    VerificationStatus
                    .VERIFIED
                ),
                evidence=list(
                    finding.evidence
                ),
                notes=(
                    "Finding contains "
                    "multiple direct code "
                    "evidence items and was "
                    "reported as CONFIRMED."
                ),
            )

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
            targets=[str(test_file)],
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

    def _classify_test_execution(
        self,
        execution: PytestExecutionResult,
    ) -> str:
        """
        Distinguish a real assertion mismatch from failures
        that do not prove a product defect.
        """

        if execution.analyzer_result.exit_code == 0:
            return (
                "EXPECTED_BEHAVIOR_CONFIRMED"
            )

        combined_output = (
            f"{execution.analyzer_result.stdout}\n"
            f"{execution.analyzer_result.stderr}"
        ).lower()

        infrastructure_markers = (
            "modulenotfounderror",
            "importerror",
            "syntaxerror",
            "fixture ",
            "fixture not found",
            "collection error",
            "error collecting",
            "connection refused",
            "database is unavailable",
            "could not connect",
            "timeout",
            "internalerror",
            "permissionerror",
            "filenotfounderror",
        )

        if any(
            marker
            in combined_output
            for marker
            in infrastructure_markers
        ):
            return (
                "ENVIRONMENT_OR_TEST_FAILURE"
            )

        if (
            execution.summary
            and execution.summary.failed
            > 0
            and execution.summary.errors
            == 0
        ):
            return (
                "PRODUCT_DEFECT_REPRODUCED"
            )

        if (
            execution.summary
            and execution.summary.errors
            > 0
        ):
            return (
                "ENVIRONMENT_OR_TEST_FAILURE"
            )

        return (
            "UNKNOWN_TEST_FAILURE"
        )

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
