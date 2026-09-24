from __future__ import annotations

from models import (
    ChangedFile,
    Confidence,
    Finding,
    FindingOrigin,
    Review,
    Severity,
    VerificationStatus,
)

from github.review_mapper import (
    build_github_review_payload,
)


def make_finding(
    *,
    finding_id: str,
    file: str,
    line: int,
    status: VerificationStatus = (
        VerificationStatus.VERIFIED
    ),
) -> Finding:
    return Finding(
        id=finding_id,
        category="LOGIC_ERROR",
        title="Synthetic finding",
        description="Synthetic review finding.",
        severity=Severity.HIGH,
        confidence=Confidence.CONFIRMED,
        file=file,
        line=line,
        evidence=[
            "Synthetic evidence."
        ],
        impact="Incorrect behavior.",
        recommendation="Fix the issue.",
        verification_status=status,
        origin=(
            FindingOrigin
            .INTRODUCED_BY_PR
        ),
        reviewer="code-review",
    )


def make_review(
    findings: list[Finding],
) -> Review:
    return Review(
        pr_id="example-project-pr-42",
        summary="Synthetic review.",
        findings=findings,
        reviewers_executed=[
            "code-review",
        ],
    )


def make_changed_file() -> ChangedFile:
    return ChangedFile(
        filename="app/service.py",
        status="modified",
        additions=2,
        deletions=1,
        changes=3,
        patch="""@@ -10,3 +10,4 @@
 line one
-line two
+line two changed
+line three
 line four
""",
    )


def test_valid_changed_line_becomes_inline_comment():
    finding = make_finding(
        finding_id="CODE-001",
        file="app/service.py",
        line=11,
    )

    payload = build_github_review_payload(
        make_review(
            [finding]
        ),
        changed_files=[
            make_changed_file()
        ],
        commit_id="head123",
    )

    assert len(
        payload.comments
    ) == 1

    comment = payload.comments[0]

    assert (
        comment.path
        == "app/service.py"
    )

    assert (
        comment.line
        == 11
    )


def test_line_outside_diff_does_not_become_inline_comment():
    finding = make_finding(
        finding_id="CODE-002",
        file="app/service.py",
        line=100,
    )

    payload = build_github_review_payload(
        make_review(
            [finding]
        ),
        changed_files=[
            make_changed_file()
        ],
    )

    assert (
        payload.comments
        == []
    )


def test_file_not_changed_does_not_become_inline_comment():
    finding = make_finding(
        finding_id="CODE-003",
        file="app/other.py",
        line=11,
    )

    payload = build_github_review_payload(
        make_review(
            [finding]
        ),
        changed_files=[
            make_changed_file()
        ],
    )

    assert (
        payload.comments
        == []
    )


def test_missing_patch_does_not_create_inline_comment():
    finding = make_finding(
        finding_id="CODE-004",
        file="app/service.py",
        line=11,
    )

    changed_file = (
        make_changed_file()
    )

    changed_file.patch = None

    payload = build_github_review_payload(
        make_review(
            [finding]
        ),
        changed_files=[
            changed_file
        ],
    )

    assert (
        payload.comments
        == []
    )


def test_refuted_finding_never_becomes_inline_comment():
    finding = make_finding(
        finding_id="CODE-005",
        file="app/service.py",
        line=11,
        status=(
            VerificationStatus.REFUTED
        ),
    )

    payload = build_github_review_payload(
        make_review(
            [finding]
        ),
        changed_files=[
            make_changed_file()
        ],
    )

    assert (
        payload.comments
        == []
    )


def test_summary_is_generated_even_without_inline_comments():
    finding = make_finding(
        finding_id="CODE-006",
        file="app/service.py",
        line=100,
    )

    payload = build_github_review_payload(
        make_review(
            [finding]
        ),
        changed_files=[
            make_changed_file()
        ],
    )

    assert payload.body
    assert (
        "PR Guardian Review"
        in payload.body
    )


def test_commit_id_is_preserved():
    payload = build_github_review_payload(
        make_review(
            []
        ),
        changed_files=[],
        commit_id="abc123",
    )

    assert (
        payload.commit_id
        == "abc123"
    )


def test_event_is_preserved():
    payload = build_github_review_payload(
        make_review(
            []
        ),
        changed_files=[],
        event="COMMENT",
    )

    assert (
        payload.event
        == "COMMENT"
    )