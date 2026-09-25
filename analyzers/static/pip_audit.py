from __future__ import annotations

import json
from pathlib import Path

from analyzers.base import (
    AnalyzerIssue,
    AnalyzerResult,
    AnalyzerStatus,
)
from analyzers.runner import run_command


class PipAuditAnalyzer:
    name = "pip-audit"

    def analyze(
        self,
        repository_path: Path,
        *,
        timeout: float = 180.0,
    ) -> AnalyzerResult:
        command = [
            "pip-audit",
            "--format",
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
                "\nUnable to parse pip-audit JSON output."
            )
            return result

        issues: list[AnalyzerIssue] = []

        dependencies = (
            payload
            if isinstance(payload, list)
            else payload.get(
                "dependencies",
                [],
            )
        )

        for dependency in dependencies:
            package = dependency.get(
                "name",
                "unknown"
            )

            version = dependency.get(
                "version",
                "unknown"
            )

            for vulnerability in dependency.get(
                "vulns",
                [],
            ):
                aliases = vulnerability.get(
                    "aliases",
                    [],
                )

                fix_versions = vulnerability.get(
                    "fix_versions",
                    [],
                )

                issues.append(
                    AnalyzerIssue(
                        tool=self.name,
                        rule_id=vulnerability.get(
                            "id"
                        ),
                        message=(
                            f"{package} {version} "
                            f"is affected by "
                            f"{vulnerability.get('id')}"
                        ),
                        severity=None,
                        metadata={
                            "package": package,
                            "version": version,
                            "aliases": aliases,
                            "fix_versions": fix_versions,
                            "description": (
                                vulnerability.get(
                                    "description"
                                )
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
