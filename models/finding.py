from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Confidence(str, Enum):
    CONFIRMED = "CONFIRMED"
    LIKELY = "LIKELY"
    POTENTIAL = "POTENTIAL"
    INFORMATIONAL = "INFORMATIONAL"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    REFUTED = "REFUTED"


class FindingOrigin(str, Enum):
    INTRODUCED_BY_PR = "INTRODUCED_BY_PR"
    EXPOSED_BY_PR = "EXPOSED_BY_PR"
    PRE_EXISTING = "PRE_EXISTING"
    UNCERTAIN = "UNCERTAIN"


class FindingPriority(str, Enum):
    BLOCKING = "BLOCKING"
    NON_BLOCKING = "NON_BLOCKING"
    ADVISORY = "ADVISORY"


@dataclass(slots=True)
class Finding:
    id: str
    category: str
    title: str
    description: str

    severity: Severity
    confidence: Confidence

    file: str | None = None
    line: int | None = None

    evidence: list[str] = field(default_factory=list)

    impact: str | None = None
    recommendation: str | None = None

    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    origin: FindingOrigin = FindingOrigin.UNCERTAIN
    priority: FindingPriority | None = None

    source: str | None = None
    sink: str | None = None

    reviewer: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def is_publishable(self) -> bool:
        if self.verification_status == VerificationStatus.REFUTED:
            return False

        return not (
            self.confidence == Confidence.POTENTIAL
            and self.severity in {Severity.LOW, Severity.INFO}
            and self.verification_status == VerificationStatus.UNVERIFIED
        )

    def is_blocking(self) -> bool:
        return self.priority == FindingPriority.BLOCKING

    def is_verified(self) -> bool:
        return self.verification_status == VerificationStatus.VERIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "file": self.file,
            "line": self.line,
            "evidence": self.evidence,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "verification_status": self.verification_status.value,
            "origin": self.origin.value,
            "priority": self.priority.value if self.priority else None,
            "source": self.source,
            "sink": self.sink,
            "reviewer": self.reviewer,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        priority = data.get("priority")

        return cls(
            id=data["id"],
            category=data["category"],
            title=data["title"],
            description=data["description"],
            severity=Severity(data["severity"]),
            confidence=Confidence(data["confidence"]),
            file=data.get("file"),
            line=data.get("line"),
            evidence=data.get("evidence", []),
            impact=data.get("impact"),
            recommendation=data.get("recommendation"),
            verification_status=VerificationStatus(
                data.get(
                    "verification_status",
                    VerificationStatus.UNVERIFIED.value,
                )
            ),
            origin=FindingOrigin(
                data.get(
                    "origin",
                    FindingOrigin.UNCERTAIN.value,
                )
            ),
            priority=FindingPriority(priority) if priority else None,
            source=data.get("source"),
            sink=data.get("sink"),
            reviewer=data.get("reviewer"),
            metadata=data.get("metadata", {}),
        )
