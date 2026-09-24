from **future** import annotations

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

```
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
```

@dataclass(slots=True)
class AnalyzerResult:
analyzer: str
status: AnalyzerStatus

```
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
def successful(self) -> bool:
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
```