from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .finding import VerificationStatus


class VerificationMethod(str, Enum):
    DIRECT_CODE_EVIDENCE = "DIRECT_CODE_EVIDENCE"
    EXISTING_TEST = "EXISTING_TEST"
    GENERATED_REGRESSION_TEST = "GENERATED_REGRESSION_TEST"
    STATIC_ANALYZER = "STATIC_ANALYZER"
    SECURITY_ANALYZER = "SECURITY_ANALYZER"
    TYPE_CHECKER = "TYPE_CHECKER"
    DEPENDENCY_ANALYZER = "DEPENDENCY_ANALYZER"
    API_SPEC_COMPARISON = "API_SPEC_COMPARISON"
    MIGRATION_EXECUTION = "MIGRATION_EXECUTION"
    DATABASE_INTEGRATION_TEST = "DATABASE_INTEGRATION_TEST"
    QUEUE_EXECUTION_TEST = "QUEUE_EXECUTION_TEST"
    MANUAL_REPOSITORY_TRACE = "MANUAL_REPOSITORY_TRACE"


@dataclass(slots=True)
class VerificationResult:
    finding_id: str
    method: VerificationMethod
    status: VerificationStatus

    evidence: list[str] = field(default_factory=list)

    command: str | None = None
    test_file: str | None = None

    expected_result: str | None = None
    actual_result: str | None = None

    notes: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "method": self.method.value,
            "status": self.status.value,
            "evidence": self.evidence,
            "command": self.command,
            "test_file": self.test_file,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationResult:
        return cls(
            finding_id=data["finding_id"],
            method=VerificationMethod(data["method"]),
            status=VerificationStatus(data["status"]),
            evidence=data.get("evidence", []),
            command=data.get("command"),
            test_file=data.get("test_file"),
            expected_result=data.get("expected_result"),
            actual_result=data.get("actual_result"),
            notes=data.get("notes"),
            metadata=data.get("metadata", {}),
        )
