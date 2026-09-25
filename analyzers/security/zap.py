from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from analyzers.base import (
    AnalyzerIssue,
    AnalyzerResult,
    AnalyzerStatus,
)
from analyzers.runner import run_command


@dataclass(slots=True)
class ZapAlert:
    alert: str
    risk: str | None = None
    confidence: str | None = None

    url: str | None = None
    parameter: str | None = None

    description: str | None = None
    solution: str | None = None

    references: list[str] = field(
        default_factory=list
    )

class ZapAnalyzer:
    """
    Passive/baseline OWASP ZAP integration.

    This analyzer is intentionally conservative.

    It must not perform active attacks unless a future explicit workflow
    enables them against an authorized local or staging target.
    """

    name = "zap"

    def __init__(
        self,
        *,
        executable: str = "zap-baseline.py",
    ) -> None:
        self.executable = executable

    def analyze(
        self,
        repository_path: Path,
        *,
        target_url: str,
        timeout: float = 600.0,
        report_file: str = ".pr_guardian_zap.json",
        allow_remote_target: bool = False,
    ) -> AnalyzerResult:
        self._validate_target(
            target_url,
            allow_remote_target=allow_remote_target,
        )

        command = [
            self.executable,
            "-t",
            target_url,
            "-J",
            report_file,
            "-I",
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

        report_path = (
            repository_path
            / report_file
        )

        if not report_path.exists():
            result.status = AnalyzerStatus.FAILED
            result.stderr += (
                "\nZAP JSON report was not generated."
            )

            return result

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
                "\nUnable to parse ZAP JSON report."
            )

            return result

        alerts = self._extract_alerts(
            payload
        )

        result.issues = [
            self._alert_to_issue(alert)
            for alert in alerts
        ]

        result.raw_output_path = report_path

        result.status = (
            AnalyzerStatus.FINDINGS
            if result.issues
            else AnalyzerStatus.SUCCESS
        )

        return result

    @staticmethod
    def _validate_target(
        target_url: str,
        *,
        allow_remote_target: bool,
    ) -> None:
        parsed = urlparse(
            target_url
        )

        if parsed.scheme not in {
            "http",
            "https",
        }:
            raise ValueError(
                "ZAP target must use HTTP or HTTPS."
            )

        hostname = (
            parsed.hostname or ""
        ).lower()

        local_hosts = {
            "localhost",
            "127.0.0.1",
            "::1",
        }

        if (
            hostname not in local_hosts
            and not allow_remote_target
        ):
            raise ValueError(
                "Remote ZAP targets are disabled by default. "
                "Use only explicitly authorized local or staging targets."
            )

    @staticmethod
    def _extract_alerts(
        payload: dict,
    ) -> list[ZapAlert]:
        results: list[ZapAlert] = []

        for site in payload.get(
            "site",
            [],
        ):
            alerts = site.get(
                "alerts",
                [],
            )

            for item in alerts:
                references = []

                reference = item.get(
                    "reference"
                )

                if reference:
                    references = [
                        line.strip()
                        for line in str(
                            reference
                        ).splitlines()
                        if line.strip()
                    ]

                instances = item.get(
                    "instances",
                    [],
                )

                if not instances:
                    results.append(
                        ZapAlert(
                            alert=item.get(
                                "alert",
                                "Unknown ZAP alert",
                            ),
                            risk=item.get(
                                "riskdesc"
                            ),
                            confidence=item.get(
                                "confidence"
                            ),
                            description=item.get(
                                "desc"
                            ),
                            solution=item.get(
                                "solution"
                            ),
                            references=references,
                        )
                    )

                    continue

                for instance in instances:
                    results.append(
                        ZapAlert(
                            alert=item.get(
                                "alert",
                                "Unknown ZAP alert",
                            ),
                            risk=item.get(
                                "riskdesc"
                            ),
                            confidence=item.get(
                                "confidence"
                            ),
                            url=instance.get(
                                "uri"
                            ),
                            parameter=instance.get(
                                "param"
                            ),
                            description=item.get(
                                "desc"
                            ),
                            solution=item.get(
                                "solution"
                            ),
                            references=references,
                        )
                    )

        return results

    def _alert_to_issue(
        self,
        alert: ZapAlert,
    ) -> AnalyzerIssue:
        return AnalyzerIssue(
            tool=self.name,
            rule_id=None,
            message=alert.alert,
            severity=alert.risk,
            metadata={
                "confidence": alert.confidence,
                "url": alert.url,
                "parameter": alert.parameter,
                "description": alert.description,
                "solution": alert.solution,
                "references": alert.references,
            },
        )
