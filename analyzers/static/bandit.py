from __future__ import annotations

import json
from pathlib import Path

from analyzers.base import (
    AnalyzerIssue,
    AnalyzerResult,
    AnalyzerStatus,
)
from analyzers.runner import run_command


class BanditAnalyzer:
    name = "bandit"

    def analyze(
        self,
        repository_path: Path,
        *,
        target: str = ".",
        timeout: float = 180.0,
    ) -> AnalyzerResult:
        command = [
            "bandit",
            "-r",
            target,
            "-f",
            "json",
        ]

        result = run_command(
            analyzer=self.name,
            command=command,
            cwd=repository_path,
            timeout=timeout,
        )

        if result.status in {
            AnalyzerStatus.NOT_INSTALLED,
            AnalyzerStatus.TIMEOUT,
            AnalyzerStatus.FAILED,
        }:
            return result

        try:
            payload = json.loads(
                result.stdout or "{}"
            )
        except json.JSONDecodeError:
            result.status = AnalyzerStatus.FAILED
            result.stderr += (
                "\nUnable to parse Bandit JSON output."
            )
            return result

        issues: list[AnalyzerIssue] = []

        for item in payload.get(
            "results",
            [],
        ):
            issues.append(
                AnalyzerIssue(
                    tool=self.name,
                    rule_id=item.get(
                        "test_id"
                    ),
                    message=item.get(
                        "issue_text",
                        "",
                    ),
                    file=item.get(
                        "filename"
                    ),
                    line=item.get(
                        "line_number"
                    ),
                    severity=item.get(
                        "issue_severity"
                    ),
                    metadata={
                        "confidence": item.get(
                            "issue_confidence"
                        ),
                        "test_name": item.get(
                            "test_name"
                        ),
                        "code": item.get(
                            "code"
                        ),
                    },
                )
            )

        result.issues = issues

        result.status = (
            AnalyzerStatus.FINDINGS
            if issues
            else AnalyzerStatus.SUCCESS
        )

        return result
