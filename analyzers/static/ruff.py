from __future__ import annotations

import json
from pathlib import Path

from analyzers.base import (
    AnalyzerIssue,
    AnalyzerResult,
    AnalyzerStatus,
    )
from analyzers.runner import run_command

class RuffAnalyzer:
    name = "ruff"

    def analyze(
        self,
        repository_path: Path,
        *,
        target: str = ".",
        timeout: float = 120.0,
    ) -> AnalyzerResult:
        command = [
            "ruff",
            "check",
            target,
            "--output-format",
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
                result.stdout or "[]"
            )
        except json.JSONDecodeError:
            result.status = AnalyzerStatus.FAILED
            result.stderr += (
                "\nUnable to parse Ruff JSON output."
            )
            return result

        issues: list[AnalyzerIssue] = []

        for item in payload:
            location = item.get(
                "location",
                {},
            )

            issues.append(
                AnalyzerIssue(
                    tool=self.name,
                    rule_id=item.get("code"),
                    message=item.get(
                        "message",
                        "",
                    ),
                    file=item.get("filename"),
                    line=location.get("row"),
                    column=location.get("column"),
                    metadata={
                        "fix": item.get("fix"),
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
