from __future__ import annotations

from models import Review, VerificationStatus

from .diff_mapper import is_valid_inline_location
from .reviews import (
    GitHubReviewComment,
    GitHubReviewPayload,
)


def build_github_review_payload(
    review: Review,
    *,
    changed_files=None,
    commit_id: str | None = None,
    event: str = "COMMENT",
) -> GitHubReviewPayload:
    comments: list[GitHubReviewComment] = []

    files_by_name = {
        file.filename: file
        for file in (changed_files or [])
    }

    for finding in review.publishable_findings():
        if finding.file is None or finding.line is None:
            continue

        if (
            finding.verification_status
            == VerificationStatus.REFUTED
        ):
            continue

        changed_file = files_by_name.get(
            finding.file
        )

        if changed_file is None:
            continue

        if not is_valid_inline_location(
            filename=finding.file,
            line_number=finding.line,
            patch=changed_file.patch,
        ):
            continue

        body = _build_inline_comment(
            finding
        )

        comments.append(
            GitHubReviewComment(
                path=finding.file,
                line=finding.line,
                body=body,
            )
        )

    summary = _build_summary(
        review
    )

    return GitHubReviewPayload(
        body=summary,
        event=event,
        commit_id=commit_id,
        comments=comments,
    )


def _build_inline_comment(
    finding,
) -> str:
    parts = [
        (
            f"**{finding.severity.value} · "
            f"{finding.confidence.value} · "
            f"{finding.verification_status.value}**"
        ),
        "",
        f"**{finding.title}**",
        "",
        finding.description,
    ]

    if finding.impact:
        parts.extend(
            [
                "",
                f"**Impact:** {finding.impact}",
            ]
        )

    if finding.recommendation:
        parts.extend(
            [
                "",
                (
                    "**Recommendation:** "
                    f"{finding.recommendation}"
                ),
            ]
        )

    if finding.evidence:
        parts.extend(
            [
                "",
                "**Evidence:**",
            ]
        )

        for item in finding.evidence[:3]:
            parts.append(
                f"- {item}"
            )

    return "\n".join(
        parts
    )


def _build_summary(
    review: Review,
) -> str:
    publishable = (
        review.publishable_findings()
    )

    blocking = (
        review.blocking_findings()
    )

    lines = [
        "## PR Guardian Review",
        "",
        review.summary,
        "",
        "### Review Summary",
        "",
        (
            "- Publishable findings: "
            f"{len(publishable)}"
        ),
        (
            "- Blocking findings: "
            f"{len(blocking)}"
        ),
        (
            "- Reviewers executed: "
            f"{len(review.reviewers_executed)}"
        ),
    ]

    verified = sum(
        1
        for finding in publishable
        if finding.is_verified()
    )

    lines.append(
        (
            "- Verified findings: "
            f"{verified}"
        )
    )

    inline_candidates = sum(
        1
        for finding in publishable
        if (
            finding.file is not None
            and finding.line is not None
        )
    )

    lines.append(
        (
            "- Inline candidates: "
            f"{inline_candidates}"
        )
    )

    return "\n".join(
        lines
    )