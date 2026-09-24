from **future** import annotations

from dataclasses import dataclass, field
from typing import Any

from .finding import Finding

@dataclass(slots=True)
class Review:
pr_id: str
summary: str

```
findings: list[Finding] = field(default_factory=list)

reviewers_executed: list[str] = field(default_factory=list)

metrics: dict[str, Any] = field(default_factory=dict)

metadata: dict[str, Any] = field(default_factory=dict)

def publishable_findings(self) -> list[Finding]:
    return [
        finding
        for finding in self.findings
        if finding.is_publishable()
    ]

def blocking_findings(self) -> list[Finding]:
    return [
        finding
        for finding in self.publishable_findings()
        if finding.is_blocking()
    ]

def inline_findings(self) -> list[Finding]:
    return [
        finding
        for finding in self.publishable_findings()
        if finding.file is not None and finding.line is not None
    ]

def to_dict(self) -> dict[str, Any]:
    return {
        "pr_id": self.pr_id,
        "summary": self.summary,
        "findings": [
            finding.to_dict()
            for finding in self.findings
        ],
        "reviewers_executed": self.reviewers_executed,
        "metrics": self.metrics,
        "metadata": self.metadata,
    }
```