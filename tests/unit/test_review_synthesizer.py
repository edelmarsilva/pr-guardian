from __future__ import annotations

from guardian.review_synthesizer import DefaultReviewSynthesizer
from models import (
    Confidence,
    Finding,
    FindingOrigin,
    FindingPriority,
    PullRequest,
    ReviewMetrics,
    Severity,
    VerificationResult,
    VerificationStatus,
    VerificationMethod,
)


def make_pull_request() -> PullRequest:
    return PullRequest(
        repository_owner="example",
        repository_name="project",
        number=42,
        title="Synthetic PR",
        description="Synthetic review synthesizer test.",
        base_branch="main",
        head_branch="feature/test",
        base_sha="base123",
        head_sha="head456",
        additions=10,
        deletions=2,
        changed_files_count=2,
        commit_count=1,
        changed_files=[],
    )


def make_finding(
    *,
    finding_id: str,
    title: str,
    category: str = "LOGIC_ERROR",
    severity: Severity = Severity.MEDIUM,
    confidence: Confidence = Confidence.LIKELY,
    file: str = "app/service.py",
    line: int = 20,
    description: str = "Synthetic defect.",
    evidence: list[str] | None = None,
    impact: str = "Incorrect behavior.",
    recommendation: str = "Fix the affected logic.",
    verification_status: VerificationStatus = (
        VerificationStatus.UNVERIFIED
    ),
    reviewer: str = "code-review",
    root_cause: str | None = None,
) -> Finding:
    metadata = {}

    if root_cause:
        metadata["root_cause"] = root_cause

    return Finding(
        id=finding_id,
        category=category,
        title=title,
        description=description,
        severity=severity,
        confidence=confidence,
        file=file,
        line=line,
        evidence=evidence or ["Synthetic evidence"],
        impact=impact,
        recommendation=recommendation,
        verification_status=verification_status,
        origin=FindingOrigin.INTRODUCED_BY_PR,
        reviewer=reviewer,
        metadata=metadata,
    )


def make_verification(
    finding_id: str,
    status: VerificationStatus,
) -> VerificationResult:
    return VerificationResult(
        finding_id=finding_id,
        method=VerificationMethod.DIRECT_CODE_EVIDENCE,
        status=status,
        evidence=["Verification evidence"],
        notes="Synthetic verification result.",
    )


def synthesize(
    findings: list[Finding],
    verifications: list[VerificationResult] | None = None,
):
    synthesizer = DefaultReviewSynthesizer()

    return synthesizer.synthesize(
        pull_request=make_pull_request(),
        context=None,
        findings=findings,
        verifications=verifications or [],
        reviewers_executed=[
            "code-review",
            "security-review",
            "test-impact",
        ],
        metrics=ReviewMetrics(
            files_changed=2,
            initial_findings=len(findings),
        ),
    )


def test_refuted_finding_is_removed_from_final_review():
    finding = make_finding(
        finding_id="SEC-001",
        title="Possible authorization bypass",
        category="AUTHORIZATION",
        severity=Severity.HIGH,
    )

    review = synthesize(
        [finding],
        [
            make_verification(
                "SEC-001",
                VerificationStatus.REFUTED,
            )
        ],
    )

    assert review.findings == []


def test_verified_finding_remains_publishable():
    finding = make_finding(
        finding_id="SEC-001",
        title="Cross-tenant access is possible",
        category="TENANT_ISOLATION",
        severity=Severity.HIGH,
        confidence=Confidence.LIKELY,
    )

    review = synthesize(
        [finding],
        [
            make_verification(
                "SEC-001",
                VerificationStatus.VERIFIED,
            )
        ],
    )

    assert len(review.findings) == 1

    final_finding = review.findings[0]

    assert (
        final_finding.verification_status
        == VerificationStatus.VERIFIED
    )


def test_verified_high_severity_finding_becomes_blocking():
    finding = make_finding(
        finding_id="SEC-002",
        title="Tenant authorization bypass",
        category="TENANT_ISOLATION",
        severity=Severity.HIGH,
    )

    review = synthesize(
        [finding],
        [
            make_verification(
                "SEC-002",
                VerificationStatus.VERIFIED,
            )
        ],
    )

    final_finding = review.findings[0]

    assert (
        final_finding.priority
        == FindingPriority.BLOCKING
    )


def test_low_severity_unverified_finding_is_not_blocking():
    finding = make_finding(
        finding_id="CODE-001",
        title="Minor validation concern",
        severity=Severity.LOW,
        confidence=Confidence.POTENTIAL,
    )

    review = synthesize(
        [finding]
    )

    if review.findings:
        assert (
            review.findings[0].priority
            != FindingPriority.BLOCKING
        )


def test_duplicate_findings_with_same_root_cause_are_consolidated():
    security_finding = make_finding(
        finding_id="SEC-001",
        title="Report lookup ignores organization",
        category="TENANT_ISOLATION",
        severity=Severity.HIGH,
        reviewer="security-review",
        root_cause=(
            "report lookup missing organization scope"
        ),
        evidence=[
            "Repository lookup uses report_id only."
        ],
    )

    code_finding = make_finding(
        finding_id="CODE-004",
        title="Organization ID is not used",
        category="LOGIC_ERROR",
        severity=Severity.HIGH,
        reviewer="code-review",
        root_cause=(
            "report lookup missing organization scope"
        ),
        evidence=[
            "organization_id is read but never passed to repository."
        ],
    )

    review = synthesize(
        [
            security_finding,
            code_finding,
        ]
    )

    assert len(review.findings) == 1


def test_deduplication_preserves_combined_evidence():
    first = make_finding(
        finding_id="SEC-001",
        title="Missing organization scope",
        category="TENANT_ISOLATION",
        severity=Severity.HIGH,
        reviewer="security-review",
        root_cause="missing tenant scope",
        evidence=[
            "Repository query filters by id only."
        ],
    )

    second = make_finding(
        finding_id="TEST-003",
        title="Cross-tenant scenario is untested",
        category="TENANT_ISOLATION",
        severity=Severity.MEDIUM,
        reviewer="test-impact",
        root_cause="missing tenant scope",
        evidence=[
            "No test verifies organization isolation."
        ],
    )

    review = synthesize(
        [
            first,
            second,
        ]
    )

    assert len(review.findings) == 1

    evidence = review.findings[0].evidence

    assert (
        "Repository query filters by id only."
        in evidence
    )

    assert (
        "No test verifies organization isolation."
        in evidence
    )


def test_deduplication_preserves_source_reviewers():
    first = make_finding(
        finding_id="SEC-001",
        title="Missing tenant scope",
        reviewer="security-review",
        root_cause="missing tenant scope",
    )

    second = make_finding(
        finding_id="CODE-001",
        title="Tenant ID ignored",
        reviewer="code-review",
        root_cause="missing tenant scope",
    )

    review = synthesize(
        [
            first,
            second,
        ]
    )

    final_finding = review.findings[0]

    source_reviewers = final_finding.metadata.get(
        "source_reviewers",
        [],
    )

    assert "security-review" in source_reviewers
    assert "code-review" in source_reviewers


def test_distinct_root_causes_remain_separate():
    authorization = make_finding(
        finding_id="SEC-001",
        title="Missing tenant scope",
        category="TENANT_ISOLATION",
        severity=Severity.HIGH,
        root_cause="missing tenant scope",
    )

    sql_injection = make_finding(
        finding_id="SEC-002",
        title="Unsafe SQL interpolation",
        category="SQL_INJECTION",
        severity=Severity.HIGH,
        file="app/repositories/users.py",
        line=45,
        root_cause="untrusted input concatenated into SQL",
    )

    review = synthesize(
        [
            authorization,
            sql_injection,
        ]
    )

    assert len(review.findings) == 2


def test_verified_finding_is_sorted_before_unverified_finding():
    unverified = make_finding(
        finding_id="CODE-001",
        title="Possible regression",
        severity=Severity.MEDIUM,
    )

    verified = make_finding(
        finding_id="SEC-001",
        title="Confirmed authorization bypass",
        severity=Severity.HIGH,
    )

    review = synthesize(
        [
            unverified,
            verified,
        ],
        [
            make_verification(
                "SEC-001",
                VerificationStatus.VERIFIED,
            )
        ],
    )

    assert review.findings[0].id == "SEC-001"


def test_multiple_refuted_findings_do_not_reach_final_review():
    findings = [
        make_finding(
            finding_id="SEC-001",
            title="Possible security problem",
        ),
        make_finding(
            finding_id="CODE-001",
            title="Possible logic problem",
        ),
    ]

    verifications = [
        make_verification(
            "SEC-001",
            VerificationStatus.REFUTED,
        ),
        make_verification(
            "CODE-001",
            VerificationStatus.REFUTED,
        ),
    ]

    review = synthesize(
        findings,
        verifications,
    )

    assert review.findings == []


def test_review_summary_exists_when_findings_exist():
    finding = make_finding(
        finding_id="SEC-001",
        title="Authorization bypass",
        severity=Severity.HIGH,
    )

    review = synthesize(
        [finding]
    )

    assert review.summary
    assert isinstance(
        review.summary,
        str,
    )


def test_review_tracks_executed_reviewers():
    finding = make_finding(
        finding_id="CODE-001",
        title="Regression",
    )

    review = synthesize(
        [finding]
    )

    assert "code-review" in review.reviewers_executed
    assert "security-review" in review.reviewers_executed
    assert "test-impact" in review.reviewers_executed