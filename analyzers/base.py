from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AnalyzerStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FINDINGS = "FINDINGS"
    NOT_INSTALLED = "NOT_INSTALLED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


@dataclass(slots=True)
class AnalyzerIssue:
    tool: str
    rule_id: str | None
    message: str

    file: str | None = None
    line: int | None = None
    column: int | None = None

    severity: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "rule_id": self.rule_id,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class AnalyzerResult:
    analyzer: str
    status: AnalyzerStatus

    issues: list[AnalyzerIssue] = field(
        default_factory=list
    )

    command: list[str] = field(
        default_factory=list
    )

    exit_code: int | None = None
    duration_seconds: float = 0.0

    stdout: str = ""
    stderr: str = ""

    raw_output_path: Path | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def succeeded(self) -> bool:
        return self.status in {
            AnalyzerStatus.SUCCESS,
            AnalyzerStatus.FINDINGS,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "analyzer": self.analyzer,
            "status": self.status.value,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "command": self.command,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "raw_output_path": (
                str(self.raw_output_path)
                if self.raw_output_path
                else None
            ),
            "metadata": self.metadata,
        }


def run_command(
    *,
    analyzer: str,
    command: list[str],
    cwd: Path,
    timeout: float = 60.0,
) -> AnalyzerResult:
    import subprocess
    import time

    start = time.monotonic()
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        duration = time.monotonic() - start

        if result.returncode == 0:
            status = AnalyzerStatus.SUCCESS
        elif result.returncode == 1:
            status = AnalyzerStatus.FINDINGS
        else:
            status = AnalyzerStatus.FAILED

        return AnalyzerResult(
            analyzer=analyzer,
            status=status,
            command=command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=duration,
        )

    except FileNotFoundError:
        duration = time.monotonic() - start
        return AnalyzerResult(
            analyzer=analyzer,
            status=AnalyzerStatus.NOT_INSTALLED,
            command=command,
            duration_seconds=duration,
        )

    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return AnalyzerResult(
            analyzer=analyzer,
            status=AnalyzerStatus.TIMEOUT,
            command=command,
            duration_seconds=duration,
        )
