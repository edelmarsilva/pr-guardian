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
class FileCoverage:
    file: str
    covered_lines: int
    missing_lines: int
    percent_covered: float

    missing_line_numbers: list[int] = field(
        default_factory=list
    )

@dataclass(slots=True)
class CoverageSummary:
    covered_lines: int = 0
    missing_lines: int = 0
    percent_covered: float = 0.0

    files: list[FileCoverage] = field(
        default_factory=list
    )

@dataclass(slots=True)
class CoverageExecutionResult:
    analyzer_result: AnalyzerResult
    summary: CoverageSummary

class CoverageAnalyzer:
    name = "coverage"

    def run(
        self,
        repository_path: Path,
        *,
        targets: list[str] | None = None,
        source: str | None = None,
        timeout: float = 300.0,
        json_file: str = ".pr_guardian_coverage.json",
    ) -> CoverageExecutionResult:
        targets = targets or []

        pytest_command = [
            "pytest",
            *targets,
            "--cov",
        ]

        if source:
            pytest_command[-1] = (
                f"--cov={source}"
            )

        pytest_command.extend(
            [
                "--cov-report=term",
                f"--cov-report=json:{json_file}",
                "-q",
            ]
        )

        result = run_command(
            analyzer=self.name,
            command=pytest_command,
            cwd=repository_path,
            timeout=timeout,
        )

        summary = CoverageSummary()

        if result.status in {
            AnalyzerStatus.NOT_INSTALLED,
            AnalyzerStatus.TIMEOUT,
            AnalyzerStatus.FAILED,
        }:
            return CoverageExecutionResult(
                analyzer_result=result,
                summary=summary,
            )

        coverage_path = (
            repository_path
            / json_file
        )

        if not coverage_path.exists():
            result.status = (
                AnalyzerStatus.FAILED
            )

            result.stderr += (
                "\nCoverage JSON report was not generated."
            )

            return CoverageExecutionResult(
                analyzer_result=result,
                summary=summary,
            )

        try:
            payload = json.loads(
                coverage_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            result.status = (
                AnalyzerStatus.FAILED
            )

            result.stderr += (
                "\nUnable to parse coverage JSON report."
            )

            return CoverageExecutionResult(
                analyzer_result=result,
                summary=summary,
            )

        totals = payload.get(
            "totals",
            {},
        )

        summary.covered_lines = int(
            totals.get(
                "covered_lines",
                0,
            )
        )

        summary.missing_lines = int(
            totals.get(
                "missing_lines",
                0,
            )
        )

        summary.percent_covered = float(
            totals.get(
                "percent_covered",
                0.0,
            )
        )

        for filename, data in payload.get(
            "files",
            {},
        ).items():
            file_summary = data.get(
                "summary",
                {},
            )

            summary.files.append(
                FileCoverage(
                    file=filename,
                    covered_lines=int(
                        file_summary.get(
                            "covered_lines",
                            0,
                        )
                    ),
                    missing_lines=int(
                        file_summary.get(
                            "missing_lines",
                            0,
                        )
                    ),
                    percent_covered=float(
                        file_summary.get(
                            "percent_covered",
                            0.0,
                        )
                    ),
                    missing_line_numbers=[
                        int(line)
                        for line in data.get(
                            "missing_lines",
                            [],
                        )
                    ],
                )
            )

        if result.exit_code == 0:
            result.status = (
                AnalyzerStatus.SUCCESS
            )
        else:
            result.status = (
                AnalyzerStatus.FINDINGS
            )

        return CoverageExecutionResult(
            analyzer_result=result,
            summary=summary,
        )
