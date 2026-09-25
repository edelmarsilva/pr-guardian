from __future__ import annotations

from pathlib import Path

import pytest

from guardian.finding_verifier import (
    DefaultFindingVerifier,
    VerificationPolicy,
)
from models import (
    Confidence,
    Finding,
    FindingOrigin,
    PullRequest,
    Severity,
    VerificationMethod,
    VerificationStatus,
)


def make_pull_request() -> PullRequest:
    return PullRequest(
        repository_owner="example",
        repository_name="project",
        number=42,
        title="Synthetic PR",
        description="Synthetic verifier test.",
        base_branch="main",
        head_branch="feature/test",
        base_sha="base123",
        head_sha="head456",
        additions=10,
        deletions=2,
        changed_files_count=1,
        commit_count=1,
        changed_files=[],
    )


def make_finding(
    *,
    finding_id: str = "SEC-001",
    category: str = "AUTHORIZATION",
    severity: Severity = Severity.HIGH,
    confidence: Confidence = Confidence.LIKELY,
    file: str = "app/service.py",
    line: int = 20,
    evidence: list[str] | None = None,
    metadata: dict | None = None,
) -> Finding:
    return Finding(
        id=finding_id,
        category=category,
        title="Synthetic finding",
        description="Synthetic defect used by verifier tests.",
        severity=severity,
        confidence=confidence,
        file=file,
        line=line,
        evidence=evidence or [],
        impact="Potential incorrect or unsafe behavior.",
        recommendation="Correct the affected implementation.",
        verification_status=VerificationStatus.UNVERIFIED,
        origin=FindingOrigin.INTRODUCED_BY_PR,
        reviewer="security-review",
        metadata=metadata or {},
    )


def make_repository(
    tmp_path: Path,
) -> Path:
    repository = (
        tmp_path
        / "repository"
    )

    repository.mkdir()

    return repository


def test_confirmed_finding_with_strong_direct_evidence_can_be_verified(
    tmp_path: Path,
):
    repository = make_repository(
        tmp_path
    )

    finding = make_finding(
        confidence=Confidence.CONFIRMED,
        evidence=[
            "Repository query filters only by report_id.",
            "organization_id is never passed to the repository.",
        ],
    )

    verifier = DefaultFindingVerifier()

    results = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )

    assert len(results) == 1

    result = results[0]

    assert (
        result.status
        == VerificationStatus.VERIFIED
    )

    assert (
        result.method
        == VerificationMethod.DIRECT_CODE_EVIDENCE
    )


def test_likely_finding_without_deterministic_evidence_remains_unverified(
    tmp_path: Path,
):
    repository = make_repository(
        tmp_path
    )

    finding = make_finding(
        confidence=Confidence.LIKELY,
        evidence=[
            "Code may allow unexpected behavior."
        ],
    )

    verifier = DefaultFindingVerifier()

    results = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )

    assert len(results) == 1

    assert (
        results[0].status
        == VerificationStatus.UNVERIFIED
    )


def test_potential_finding_is_not_promoted_without_evidence(
    tmp_path: Path,
):
    repository = make_repository(
        tmp_path
    )

    finding = make_finding(
        confidence=Confidence.POTENTIAL,
        evidence=[],
    )

    verifier = DefaultFindingVerifier()

    result = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )[0]

    assert (
        result.status
        != VerificationStatus.VERIFIED
    )


def test_generated_regression_test_failure_can_verify_finding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = make_repository(
        tmp_path
    )

    test_file = (
        tmp_path
        / "reports"
        / "verification"
        / "example-project-pr-42"
        / "tests"
        / "test_sec_001.py"
    )

    test_file.parent.mkdir(
        parents=True
    )

    test_file.write_text(
        """
def test_expected_secure_behavior():
    assert False
""",
        encoding="utf-8",
    )

    finding = make_finding(
        finding_id="SEC-001",
        category="TENANT_ISOLATION",
    )

    verifier = DefaultFindingVerifier()

    monkeypatch.chdir(
        tmp_path
    )

    results = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )

    result = results[0]

    assert (
        result.method
        == VerificationMethod.GENERATED_REGRESSION_TEST
    )

    assert (
        result.status
        == VerificationStatus.VERIFIED
    )


def test_generated_regression_test_success_can_refute_finding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = make_repository(
        tmp_path
    )

    test_file = (
        tmp_path
        / "reports"
        / "verification"
        / "example-project-pr-42"
        / "tests"
        / "test_sec_002.py"
    )

    test_file.parent.mkdir(
        parents=True
    )

    test_file.write_text(
        """
def test_expected_secure_behavior():
    assert True
""",
        encoding="utf-8",
    )

    finding = make_finding(
        finding_id="SEC-002",
        category="TENANT_ISOLATION",
    )

    verifier = DefaultFindingVerifier()

    monkeypatch.chdir(
        tmp_path
    )

    result = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )[0]

    assert (
        result.method
        == VerificationMethod.GENERATED_REGRESSION_TEST
    )

    assert (
        result.status
        == VerificationStatus.REFUTED
    )


def test_broken_generated_test_must_not_be_treated_as_verified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = make_repository(
        tmp_path
    )

    test_file = (
        tmp_path
        / "reports"
        / "verification"
        / "example-project-pr-42"
        / "tests"
        / "test_sec_003.py"
    )

    test_file.parent.mkdir(
        parents=True
    )

    test_file.write_text(
        """
def test_invalid():
    this is not valid python
""",
        encoding="utf-8",
    )

    finding = make_finding(
        finding_id="SEC-003",
        category="TENANT_ISOLATION",
    )

    verifier = DefaultFindingVerifier()

    monkeypatch.chdir(
        tmp_path
    )

    result = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )[0]

    assert (
        result.status
        != VerificationStatus.VERIFIED
    )

    assert result.status in {
        VerificationStatus.VERIFICATION_FAILED,
        VerificationStatus.UNVERIFIED,
    }


def test_test_environment_failure_must_not_verify_product_defect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = make_repository(
        tmp_path
    )

    test_file = (
        tmp_path
        / "reports"
        / "verification"
        / "example-project-pr-42"
        / "tests"
        / "test_sec_004.py"
    )

    test_file.parent.mkdir(
        parents=True
    )

    test_file.write_text(
        """
import definitely_missing_dependency


def test_something():
    assert True
""",
        encoding="utf-8",
    )

    finding = make_finding(
        finding_id="SEC-004",
        category="TENANT_ISOLATION",
    )

    verifier = DefaultFindingVerifier()

    monkeypatch.chdir(
        tmp_path
    )

    result = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )[0]

    assert (
        result.status
        != VerificationStatus.VERIFIED
    )


def test_not_applicable_status_is_valid_for_informational_finding(
    tmp_path: Path,
):
    repository = make_repository(
        tmp_path
    )

    finding = make_finding(
        finding_id="INFO-001",
        category="DOCUMENTATION",
        severity=Severity.INFO,
        confidence=Confidence.INFORMATIONAL,
    )

    verifier = DefaultFindingVerifier()

    result = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )[0]

    assert result.status in {
        VerificationStatus.NOT_APPLICABLE,
        VerificationStatus.UNVERIFIED,
    }


def test_verifier_returns_one_result_per_finding(
    tmp_path: Path,
):
    repository = make_repository(
        tmp_path
    )

    findings = [
        make_finding(
            finding_id="SEC-001",
        ),
        make_finding(
            finding_id="CODE-001",
            category="LOGIC_ERROR",
        ),
        make_finding(
            finding_id="API-001",
            category="BREAKING_CHANGE",
        ),
    ]

    verifier = DefaultFindingVerifier()

    results = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=findings,
    )

    assert len(results) == len(
        findings
    )

    assert {
        result.finding_id
        for result in results
    } == {
        finding.id
        for finding in findings
    }


def test_verified_result_contains_evidence(
    tmp_path: Path,
):
    repository = make_repository(
        tmp_path
    )

    finding = make_finding(
        confidence=Confidence.CONFIRMED,
        evidence=[
            "Direct evidence one.",
            "Direct evidence two.",
        ],
    )

    verifier = DefaultFindingVerifier()

    result = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )[0]

    assert (
        result.status
        == VerificationStatus.VERIFIED
    )

    assert result.evidence


def test_refuted_finding_is_marked_refuted_on_finding_when_applied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = make_repository(
        tmp_path
    )

    test_file = (
        tmp_path
        / "reports"
        / "verification"
        / "example-project-pr-42"
        / "tests"
        / "test_code_001.py"
    )

    test_file.parent.mkdir(
        parents=True
    )

    test_file.write_text(
        """
def test_expected_behavior():
    assert True
""",
        encoding="utf-8",
    )

    finding = make_finding(
        finding_id="CODE-001",
        category="LOGIC_ERROR",
    )

    verifier = DefaultFindingVerifier()

    monkeypatch.chdir(
        tmp_path
    )

    result = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=[finding],
    )[0]

    assert (
        result.status
        == VerificationStatus.REFUTED
    )


def test_verifier_does_not_force_every_finding_to_verified(
    tmp_path: Path,
):
    repository = make_repository(
        tmp_path
    )

    findings = [
        make_finding(
            finding_id="CODE-001",
            confidence=Confidence.POTENTIAL,
            evidence=[],
        ),
        make_finding(
            finding_id="SEC-001",
            confidence=Confidence.LIKELY,
            evidence=[
                "Suspicious code path."
            ],
        ),
    ]

    verifier = DefaultFindingVerifier()

    results = verifier.verify(
        pull_request=make_pull_request(),
        context=None,
        repository_path=repository,
        findings=findings,
    )

    assert any(
        result.status
        != VerificationStatus.VERIFIED
        for result in results
    )
