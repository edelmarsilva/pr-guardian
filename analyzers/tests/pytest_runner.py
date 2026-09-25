from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

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
    failure_phase: str | None = None
    assertion_failure: bool = False
    call_outcome: str | None = None

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
            and self.analyzer_result.exit_code == 0
            and self.summary.passed > 0
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
        json_report_file: str | None = None,
    ) -> PytestExecutionResult:
        targets = targets or []
        extra_args = extra_args or []

        repository_path = Path(repository_path).resolve()
        report_path = repository_path / (
            json_report_file or f".pr_guardian_pytest_{uuid4().hex}.json"
        )
        # Explicit report paths must never reuse evidence from an earlier run.
        try:
            report_path.unlink(missing_ok=True)
        except OSError as exc:
            return PytestExecutionResult(
                analyzer_result=AnalyzerResult(
                    analyzer=self.name, status=AnalyzerStatus.FAILED, stderr=str(exc)
                ),
                summary=PytestSummary(),
            )

        command = [
            sys.executable,
            "-m",
            "pytest",
            *targets,
            "--json-report",
            f"--json-report-file={report_path}",
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
        } or (result.status == AnalyzerStatus.FAILED and result.exit_code is None):
            return PytestExecutionResult(
                analyzer_result=result,
                summary=summary,
            )

        result.raw_output_path = report_path
        if not report_path.is_file():
            result.status = AnalyzerStatus.FAILED
            result.stderr += "\nPytest did not produce a fresh JSON report."
            return PytestExecutionResult(analyzer_result=result, summary=summary)

        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Report must be an object")
            if payload.get("exitcode") != result.exit_code:
                raise ValueError("Report exit code disagrees with process")
            counts = payload.get("summary")
            tests = payload.get("tests")
            if not isinstance(counts, dict) or not isinstance(tests, list):
                raise ValueError("Report lacks summary or test results")
            for key in ("passed", "failed", "skipped", "error", "errors", "xfailed", "xpassed"):
                value = counts.get(key, 0)
                if type(value) is not int or value < 0:
                    raise ValueError("Invalid test count")
            for test in tests:
                if not isinstance(test, dict):
                    raise ValueError("Invalid test result")
                for phase in ("setup", "call", "teardown"):
                    data = test.get(phase, {})
                    if not isinstance(data, dict):
                        raise ValueError("Invalid test phase")
                    if "duration" in data and not isinstance(data["duration"], (int, float)):
                        raise ValueError("Invalid duration")
                    if "crash" in data and not isinstance(data["crash"], dict):
                        raise ValueError("Invalid crash")
        except (
            OSError,
            ValueError,
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

            failure_phase = next(
                (phase for phase in ("setup", "teardown", "call")
                 if test.get(phase, {}).get("outcome") == "failed"),
                None,
            )
            crash = (call_data or {}).get("crash", {})
            crash_message = str(crash.get("message", ""))
            # Assertion rewriting reports either `assert ...` or AssertionError.
            # Never infer an assertion from a generic failed-test count.
            assertion_failure = bool(re.match(
                r"^(?:assert\s|AssertionError(?:\b|:))", crash_message
            ))

            summary.tests.append(
                PytestTestCaseResult(
                    nodeid=test.get(
                        "nodeid",
                        "",
                    ),
                    outcome=outcome,
                    duration_seconds=duration,
                    message=message,
                    failure_phase=failure_phase,
                    assertion_failure=assertion_failure,
                    call_outcome=(call_data or {}).get("outcome"),
                )
            )

        if result.exit_code not in {0, 1}:
            result.status = AnalyzerStatus.FAILED
        elif (
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
