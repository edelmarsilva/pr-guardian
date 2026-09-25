from __future__ import annotations

from models import (
    Confidence,
    Finding,
    FindingOrigin,
    FindingPriority,
    Review,
    ReviewMetrics,
    Severity,
    VerificationMethod,
    VerificationResult,
    VerificationStatus,
)


def make_finding(
    *,
    finding_id: str = "SEC-001",
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
    priority: FindingPriority | None = None,
) -> Finding:
    return Finding(
        id=finding_id,
        category="TENANT_ISOLATION",
        title="Cross-tenant access",
        description="Synthetic finding.",
        severity=Severity.HIGH,
        confidence=Confidence.LIKELY,
        file="app/repositories.py",
        line=20,
        evidence=[
            "Repository lookup ignores organization_id.",
        ],
        impact="Cross-tenant data access may be possible.",
        recommendation="Scope lookup by organization.",
        verification_status=verification_status,
        origin=FindingOrigin.INTRODUCED_BY_PR,
        priority=priority,
        reviewer="security-review",
        metadata={
            "root_cause": "missing tenant scope",
        },
    )


def test_finding_serializes_to_dictionary():
    finding = make_finding()

    payload = finding.to_dict()

    assert payload["id"] == "SEC-001"
    assert payload["severity"] == "HIGH"
    assert payload["confidence"] == "LIKELY"
    assert payload["verification_status"] == "UNVERIFIED"
    assert payload["origin"] == "INTRODUCED_BY_PR"


def test_finding_round_trip_serialization():
    original = make_finding(
        verification_status=VerificationStatus.VERIFIED,
        priority=FindingPriority.BLOCKING,
    )

    payload = original.to_dict()

    restored = Finding.from_dict(
        payload
    )

    assert restored.id == original.id
    assert restored.category == original.category
    assert restored.severity == original.severity
    assert restored.confidence == original.confidence
    assert (
        restored.verification_status
        == original.verification_status
    )
    assert restored.origin == original.origin
    assert restored.priority == original.priority
    assert restored.metadata == original.metadata


def test_verified_finding_is_publishable():
    finding = make_finding(
        verification_status=VerificationStatus.VERIFIED,
    )

    assert finding.is_publishable() is True


def test_unverified_finding_can_remain_publishable():
    finding = make_finding(
        verification_status=VerificationStatus.UNVERIFIED,
    )

    assert finding.is_publishable() is True


def test_refuted_finding_is_never_publishable():
    finding = make_finding(
        verification_status=VerificationStatus.REFUTED,
    )

    assert finding.is_publishable() is False


def test_verification_failed_finding_is_not_automatically_refuted():
    finding = make_finding(
        verification_status=VerificationStatus.VERIFICATION_FAILED,
    )

    assert (
        finding.verification_status
        == VerificationStatus.VERIFICATION_FAILED
    )

    assert (
        finding.verification_status
        != VerificationStatus.REFUTED
    )


def test_blocking_priority_is_detected():
    finding = make_finding(
        verification_status=VerificationStatus.VERIFIED,
        priority=FindingPriority.BLOCKING,
    )

    assert finding.is_blocking() is True


def test_non_blocking_priority_is_not_blocking():
    finding = make_finding(
        priority=FindingPriority.NON_BLOCKING,
    )

    assert finding.is_blocking() is False


def test_advisory_priority_is_not_blocking():
    finding = make_finding(
        priority=FindingPriority.ADVISORY,
    )

    assert finding.is_blocking() is False


def test_verified_helper_returns_true_only_for_verified():
    verified = make_finding(
        verification_status=VerificationStatus.VERIFIED,
    )

    refuted = make_finding(
        finding_id="SEC-002",
        verification_status=VerificationStatus.REFUTED,
    )

    unverified = make_finding(
        finding_id="SEC-003",
        verification_status=VerificationStatus.UNVERIFIED,
    )

    assert verified.is_verified() is True
    assert refuted.is_verified() is False
    assert unverified.is_verified() is False


def test_verification_result_serialization():
    result = VerificationResult(
        finding_id="SEC-001",
        method=VerificationMethod.GENERATED_REGRESSION_TEST,
        status=VerificationStatus.VERIFIED,
        evidence=[
            "Regression test reproduced the issue.",
        ],
        command="pytest test_sec_001.py",
        test_file="test_sec_001.py",
        expected_result="403",
        actual_result="200",
        notes="Cross-tenant access reproduced.",
        metadata={
            "failure_class": "PRODUCT_DEFECT",
        },
    )

    payload = result.to_dict()

    assert payload["finding_id"] == "SEC-001"
    assert (
        payload["method"]
        == "GENERATED_REGRESSION_TEST"
    )
    assert payload["status"] == "VERIFIED"
    assert payload["actual_result"] == "200"


def test_review_returns_only_publishable_findings():
    findings = [
        make_finding(
            finding_id="SEC-001",
            verification_status=VerificationStatus.VERIFIED,
        ),
        make_finding(
            finding_id="SEC-002",
            verification_status=VerificationStatus.UNVERIFIED,
        ),
        make_finding(
            finding_id="SEC-003",
            verification_status=VerificationStatus.REFUTED,
        ),
    ]

    review = Review(
        pr_id="example-project-pr-42",
        summary="Synthetic review.",
        findings=findings,
        reviewers_executed=[
            "security-review",
        ],
    )

    publishable = (
        review.publishable_findings()
    )

    ids = {
        finding.id
        for finding
        in publishable
    }

    assert "SEC-001" in ids
    assert "SEC-002" in ids
    assert "SEC-003" not in ids


def test_review_returns_only_blocking_findings():
    findings = [
        make_finding(
            finding_id="SEC-001",
            priority=FindingPriority.BLOCKING,
        ),
        make_finding(
            finding_id="CODE-001",
            priority=FindingPriority.NON_BLOCKING,
        ),
        make_finding(
            finding_id="INFO-001",
            priority=FindingPriority.ADVISORY,
        ),
    ]

    review = Review(
        pr_id="pr-42",
        summary="Synthetic review.",
        findings=findings,
        reviewers_executed=[
            "security-review",
            "code-review",
        ],
    )

    blocking = (
        review.blocking_findings()
    )

    assert len(blocking) == 1
    assert blocking[0].id == "SEC-001"


def test_inline_findings_require_file_and_line():
    valid = make_finding(
        finding_id="SEC-001",
    )

    no_line = make_finding(
        finding_id="SEC-002",
    )
    no_line.line = None

    no_file = make_finding(
        finding_id="SEC-003",
    )
    no_file.file = None

    review = Review(
        pr_id="pr-42",
        summary="Synthetic review.",
        findings=[
            valid,
            no_line,
            no_file,
        ],
        reviewers_executed=[
            "security-review",
        ],
    )

    inline = review.inline_findings()

    ids = {
        finding.id
        for finding
        in inline
    }

    assert "SEC-001" in ids
    assert "SEC-002" not in ids
    assert "SEC-003" not in ids


def test_review_serialization_preserves_metrics():
    metrics = ReviewMetrics(
        files_changed=3,
        reviewers_selected=2,
        reviewers_executed=2,
        initial_findings=4,
        verified_findings=2,
        refuted_findings=1,
        final_findings=2,
    )

    review = Review(
        pr_id="pr-42",
        summary="Synthetic review.",
        findings=[
            make_finding(),
        ],
        reviewers_executed=[
            "security-review",
        ],
        metrics=metrics.to_dict(),
    )

    payload = review.to_dict()

    assert payload["pr_id"] == "pr-42"
    assert (
        payload["metrics"]["initial_findings"]
        == 4
    )
    assert (
        payload["metrics"]["refuted_findings"]
        == 1
    )


def test_review_serialization_preserves_reviewer_information():
    review = Review(
        pr_id="pr-42",
        summary="Synthetic review.",
        findings=[
            make_finding(),
        ],
        reviewers_executed=[
            "security-review",
            "database-review",
        ],
    )

    payload = review.to_dict()

    assert payload[
        "reviewers_executed"
    ] == [
        "security-review",
        "database-review",
    ]


def test_refuted_finding_cannot_become_inline_comment():
    finding = make_finding(
        verification_status=VerificationStatus.REFUTED,
    )

    review = Review(
        pr_id="pr-42",
        summary="Synthetic review.",
        findings=[
            finding,
        ],
        reviewers_executed=[
            "security-review",
        ],
    )

    inline_ids = {
        item.id
        for item
        in review.inline_findings()
    }

    assert finding.id not in inline_ids


def test_empty_review_is_valid():
    review = Review(
        pr_id="pr-42",
        summary=(
            "No publishable findings were produced."
        ),
        findings=[],
        reviewers_executed=[
            "code-review",
        ],
    )

    assert review.findings == []
    assert review.publishable_findings() == []
    assert review.blocking_findings() == []
    assert review.inline_findings() == []
