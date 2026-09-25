from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from analyzers.base import (
    AnalyzerResult,
    AnalyzerStatus,
    )
from analyzers.runner import run_command

@dataclass(slots=True)
class PytestTestCaseResult:
    nodeid: str
    outcome: str
    duration_seconds: float | None = None
    message: str | None = None

@dataclass(slots=True)
class PytestSummary:
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    xfailed: int = 0
    xpassed: int = 0

    tests: list[PytestTestCaseResult] = field(
        default_factory=list
    )

    @property
    def total(self) -> int:
        return (
            self.passed
            + self.failed
            + self.skipped
            + self.errors
            + self.xfailed
            + self.xpassed
        )

@dataclass(slots=True)
class PytestExecutionResult:
    analyzer_result: AnalyzerResult
    summary: PytestSummary

    @property
    def successful(self) -> bool:
        return (
            self.analyzer_result.status
            in {
                AnalyzerStatus.SUCCESS,
                AnalyzerStatus.FINDINGS,
            }
            and self.summary.failed == 0
            and self.summary.errors == 0
        )

class PytestRunner:
    name = "pytest"

    def run(
        self,
        repository_path: Path,
        *,
        targets: list[str] | None = None,
        timeout: float = 300.0,
        extra_args: list[str] | None = None,
        json_report_file: str = ".pr_guardian_pytest.json",
    ) -> PytestExecutionResult:
        import sys
        targets = targets or []
        extra_args = extra_args or []

        command = [
            sys.executable,
            "-m",
            "pytest",
            *targets,
            "--json-report",
            f"--json-report-file={json_report_file}",
            "-q",
            *extra_args,
        ]

        result = run_command(
            analyzer=self.name,
            command=command,
            cwd=repository_path,
            timeout=timeout,
        )

        summary = PytestSummary()

        if result.status in {
            AnalyzerStatus.NOT_INSTALLED,
            AnalyzerStatus.TIMEOUT,
            AnalyzerStatus.FAILED,
        }:
            return PytestExecutionResult(
                analyzer_result=result,
                summary=summary,
            )

        report_path = (
            repository_path
            / json_report_file
        )

        if not report_path.exists():
            if result.exit_code == 0:
                result.status = AnalyzerStatus.SUCCESS
            else:
                result.status = AnalyzerStatus.FINDINGS

            return PytestExecutionResult(
                analyzer_result=result,
                summary=summary,
            )

        try:
            payload = json.loads(
                report_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            result.status = AnalyzerStatus.FAILED
            result.stderr += (
                "\nUnable to parse pytest JSON report."
            )

            return PytestExecutionResult(
                analyzer_result=result,
                summary=summary,
            )

        report_summary = payload.get(
            "summary",
            {},
        )

        summary.passed = report_summary.get(
            "passed",
            0,
        )

        summary.failed = report_summary.get(
            "failed",
            0,
        )

        summary.skipped = report_summary.get(
            "skipped",
            0,
        )

        summary.errors = report_summary.get(
            "error",
            report_summary.get(
                "errors",
                0,
            ),
        )

        summary.xfailed = report_summary.get(
            "xfailed",
            0,
        )

        summary.xpassed = report_summary.get(
            "xpassed",
            0,
        )

        for test in payload.get(
            "tests",
            [],
        ):
            outcome = test.get(
                "outcome",
                "unknown",
            )

            duration = None

            for phase in (
                "setup",
                "call",
                "teardown",
            ):
                phase_data = test.get(
                    phase
                )

                if not isinstance(
                    phase_data,
                    dict,
                ):
                    continue

                phase_duration = (
                    phase_data.get(
                        "duration"
                    )
                )

                if phase_duration is None:
                    continue

                duration = (
                    duration or 0.0
                ) + float(
                    phase_duration
                )

            message = None

            call_data = test.get(
                "call"
            )

            if isinstance(
                call_data,
                dict,
            ):
                longrepr = call_data.get(
                    "longrepr"
                )

                if longrepr:
                    message = str(
                        longrepr
                    )

            summary.tests.append(
                PytestTestCaseResult(
                    nodeid=test.get(
                        "nodeid",
                        "",
                    ),
                    outcome=outcome,
                    duration_seconds=duration,
                    message=message,
                )
            )

        if (
            summary.failed > 0
            or summary.errors > 0
        ):
            result.status = (
                AnalyzerStatus.FINDINGS
            )
        else:
            result.status = (
                AnalyzerStatus.SUCCESS
            )

        return PytestExecutionResult(
            analyzer_result=result,
            summary=summary,
        )
