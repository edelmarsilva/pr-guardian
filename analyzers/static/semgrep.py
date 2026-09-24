from **future** import annotations

import json
from pathlib import Path

from analyzers.base import (
AnalyzerIssue,
AnalyzerResult,
AnalyzerStatus,
)
from analyzers.runner import run_command

class SemgrepAnalyzer:
name = "semgrep"

```
def analyze(
    self,
    repository_path: Path,
    *,
    config: str = "auto",
    target: str = ".",
    timeout: float = 300.0,
) -> AnalyzerResult:
    command = [
        "semgrep",
        "scan",
        "--config",
        config,
        "--json",
        target,
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
            "\nUnable to parse Semgrep JSON output."
        )
        return result

    issues: list[AnalyzerIssue] = []

    for item in payload.get(
        "results",
        [],
    ):
        start = item.get(
            "start",
            {},
        )

        extra = item.get(
            "extra",
            {},
        )

        metadata = extra.get(
            "metadata",
            {},
        )

        issues.append(
            AnalyzerIssue(
                tool=self.name,
                rule_id=item.get(
                    "check_id"
                ),
                message=extra.get(
                    "message",
                    "",
                ),
                file=item.get(
                    "path"
                ),
                line=start.get(
                    "line"
                ),
                column=start.get(
                    "col"
                ),
                severity=extra.get(
                    "severity"
                ),
                metadata={
                    "metadata": metadata,
                    "lines": extra.get(
                        "lines"
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
```