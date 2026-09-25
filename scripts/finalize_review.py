from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from guardian import (
    DefaultFindingVerifier,
    DefaultReviewSynthesizer,
)
from models import (
    Confidence,
    Finding,
    FindingOrigin,
    PullRequest,
    ReviewMetrics,
    Severity,
    VerificationResult,
    VerificationStatus,
)
from scripts.validate_artifact import validate_artifact

SCHEMAS_ROOT = Path(__file__).resolve().parents[1] / "schemas"

def require_valid_artifact(path: Path, schema: str) -> None:
    result = validate_artifact(schema_path=SCHEMAS_ROOT / schema, artifact_path=path)
    if not result["valid"]:
        raise FinalizeReviewError(f"Invalid artifact {path}: {result['errors']}")

class FinalizeReviewError(RuntimeError):
    """Raised when final review generation cannot continue."""

def read_json(
    path: Path,
) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise FinalizeReviewError(
            f"Required file does not exist: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise FinalizeReviewError(
            f"Invalid JSON file: {path}"
        ) from exc

    if not isinstance(payload, dict):
        raise FinalizeReviewError(
            f"Expected JSON object in {path}"
        )

    return payload

def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

def write_text(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

def parse_finding(
    data: dict[str, Any],
    *,
    reviewer: str,
    ) -> Finding:
    required_fields = {
    "id",
    "category",
    "severity",
    "confidence",
    "title",
    "description",
    }

    missing = sorted(
        required_fields
        - data.keys()
    )

    if missing:
        raise FinalizeReviewError(
            
                f"Finding from {reviewer} "
                f"is missing required fields: "
                f"{', '.join(missing)}"
            
        )

    try:
        severity = Severity(
            data["severity"]
        )

        confidence = Confidence(
            data["confidence"]
        )

        verification_status = (
            VerificationStatus(
                data.get(
                    "verification_status",
                    "UNVERIFIED",
                )
            )
        )

        origin = FindingOrigin(
            data.get(
                "origin",
                "UNCERTAIN",
            )
        )

    except ValueError as exc:
        raise FinalizeReviewError(
            
                f"Finding {data.get('id')} "
                f"from {reviewer} contains "
                f"an invalid enum value."
            
        ) from exc

    evidence = data.get(
        "evidence",
        [],
    )

    if not isinstance(
        evidence,
        list,
    ):
        raise FinalizeReviewError(
            
                f"Finding {data['id']} "
                "evidence must be a list."
            
        )

    metadata = data.get(
        "metadata",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    return Finding(
        id=str(
            data["id"]
        ),
        category=str(
            data["category"]
        ),
        title=str(
            data["title"]
        ),
        description=str(
            data["description"]
        ),
        severity=severity,
        confidence=confidence,
        file=(
            str(data["file"])
            if data.get("file")
            is not None
            else None
        ),
        line=(
            int(data["line"])
            if data.get("line")
            is not None
            else None
        ),
        evidence=[
            str(item)
            for item in evidence
        ],
        impact=(
            str(data["impact"])
            if data.get("impact")
            is not None
            else None
        ),
        recommendation=(
            str(data["recommendation"])
            if data.get(
                "recommendation"
            )
            is not None
            else None
        ),
        verification_status=(
            verification_status
        ),
        origin=origin,
        source=(
            str(data["source"])
            if data.get("source")
            is not None
            else None
        ),
        sink=(
            str(data["sink"])
            if data.get("sink")
            is not None
            else None
        ),
        reviewer=reviewer,
        metadata=metadata,
    )

def load_findings(
    *,
    findings_directory: Path,
    selected_reviewers: list[str],
    ) -> list[Finding]:
    findings: list[Finding] = []

    for reviewer in selected_reviewers:
        path = (
            findings_directory
            / f"{reviewer}.json"
        )

        if not path.exists():
            raise FinalizeReviewError(
                
                    f"Selected reviewer "
                    f"'{reviewer}' did not "
                    f"produce {path}"
                
            )

        require_valid_artifact(path, "finding.schema.json")
        payload = read_json(path)
        if payload["reviewer"] != reviewer:
            raise FinalizeReviewError(f"Reviewer mismatch in {path}")

        reviewer_name = str(
            payload.get(
                "reviewer",
                reviewer,
            )
        )

        raw_findings = payload.get(
            "findings",
            [],
        )

        if not isinstance(
            raw_findings,
            list,
        ):
            raise FinalizeReviewError(
                
                    f"'findings' must be "
                    f"a list in {path}"
                
            )

        for raw_finding in (
            raw_findings
        ):
            if not isinstance(
                raw_finding,
                dict,
            ):
                raise FinalizeReviewError(
                    
                        f"Invalid finding "
                        f"entry in {path}"
                    
                )

            if raw_finding.get("reviewer", reviewer) != reviewer:
                raise FinalizeReviewError(f"Finding reviewer mismatch in {path}")
            if any(item.id == raw_finding["id"] for item in findings):
                raise FinalizeReviewError(f"Duplicate finding ID: {raw_finding['id']}")
            findings.append(
                parse_finding(
                    raw_finding,
                    reviewer=(
                        reviewer_name
                    ),
                )
            )

    return findings

def rebuild_pull_request(
    plan: dict[str, Any],
    ) -> PullRequest:
    repository_full_name = str(
    plan["repository"]
    )

    if "/" not in repository_full_name:
        raise FinalizeReviewError(
            "Invalid repository in review plan."
        )

    owner, repository = (
        repository_full_name.split(
            "/",
            1,
        )
    )

    changed_files = []

    from models import ChangedFile

    for item in plan.get(
        "changed_files",
        [],
    ):
        changed_files.append(
            ChangedFile(
                filename=str(
                    item["filename"]
                ),
                status=str(
                    item.get(
                        "status",
                        "modified",
                    )
                ),
                additions=int(
                    item.get(
                        "additions",
                        0,
                    )
                ),
                deletions=int(
                    item.get(
                        "deletions",
                        0,
                    )
                ),
                changes=(
                    int(
                        item.get(
                            "additions",
                            0,
                        )
                    )
                    +
                    int(
                        item.get(
                            "deletions",
                            0,
                        )
                    )
                ),
            )
        )

    return PullRequest(
        repository_owner=owner,
        repository_name=repository,
        number=int(
            plan["pull_number"]
        ),
        title=str(
            plan.get(
                "title",
                "",
            )
        ),
        description=plan.get(
            "description"
        ),
        base_branch="",
        head_branch="",
        base_sha=str(
            plan["base_sha"]
        ),
        head_sha=str(
            plan["head_sha"]
        ),
        additions=sum(
            item.additions
            for item in changed_files
        ),
        deletions=sum(
            item.deletions
            for item in changed_files
        ),
        changed_files_count=len(
            changed_files
        ),
        commit_count=0,
        changed_files=changed_files,
    )

def rebuild_context(
    plan: dict[str, Any],
    ):
    from guardian.context_builder import (
    PullRequestContext,
    RepositoryContext,
    )

    return PullRequestContext(
        pr_id=str(
            plan["pr_id"]
        ),
        title=str(
            plan.get(
                "title",
                "",
            )
        ),
        description=plan.get(
            "description"
        ),
        base_sha=str(
            plan["base_sha"]
        ),
        head_sha=str(
            plan["head_sha"]
        ),
        files_changed=len(
            plan.get(
                "changed_files",
                [],
            )
        ),
        changed_files=[],
        repository=RepositoryContext(
            repository_files=0,
        ),
        potentially_affected_files=list(
            plan.get(
                "potentially_affected_files",
                [],
            )
        ),
        risk_signals=list(
            plan.get(
                "risk_signals",
                [],
            )
        ),
    )

def render_review_markdown(
    review,
    ) -> str:
    lines = [
    "# Pull Request Review",
    "",
    "## Summary",
    "",
    review.summary,
    ]

    blocking = [
        finding
        for finding
        in review.findings
        if (
            finding.priority
            and finding.priority.value
            == "BLOCKING"
        )
    ]

    non_blocking = [
        finding
        for finding
        in review.findings
        if (
            not finding.priority
            or finding.priority.value
            != "BLOCKING"
        )
    ]

    if blocking:
        lines.extend(
            [
                "",
                "## Blocking Findings",
            ]
        )

        for finding in blocking:
            _append_finding(
                lines,
                finding,
            )

    if non_blocking:
        lines.extend(
            [
                "",
                "## Other Findings",
            ]
        )

        for finding in non_blocking:
            _append_finding(
                lines,
                finding,
            )

    return "\n".join(
        lines
    )

def _append_finding(
    lines: list[str],
    finding: Finding,
    ) -> None:
    lines.extend(
    [
    "",
    (
    f"### "
    f"{finding.severity.value} · "
    f"{finding.verification_status.value}"
    f" — {finding.title}"
    ),
    "",
    ]
    )

    if finding.file:
        location = finding.file

        if finding.line:
            location += (
                f":{finding.line}"
            )

        lines.extend(
            [
                f"`{location}`",
                "",
            ]
        )

    lines.append(
        finding.description
    )

    if finding.evidence:
        lines.extend(
            [
                "",
                "__Evidence__",
            ]
        )

        for item in (
            finding.evidence
        ):
            lines.append(
                f"- {item}"
            )

    if finding.impact:
        lines.extend(
            [
                "",
                (
                    "**Impact:** "
                    f"{finding.impact}"
                ),
            ]
        )

    if finding.recommendation:
        lines.extend(
            [
                "",
                (
                    "**Recommendation:** "
                    f"{finding.recommendation}"
                ),
            ]
        )

def finalize_review(
    *,
    pr_id: str,
    reports_root: Path,
    ) -> dict[str, Any]:
    started = time.perf_counter()
    raw_directory = (
    reports_root
    / "raw"
    / pr_id
    )

    plan_path = (
        raw_directory
        / "review-plan.json"
    )

    plan = read_json(
        plan_path
    )

    if plan.get("pr_id") != pr_id:
        raise FinalizeReviewError(
            "Review plan PR identifier mismatch."
        )

    selected_reviewers = list(
        plan.get(
            "selected_reviewers",
            [],
        )
    )

    from guardian.router import ReviewDomain
    allowed_reviewers = {domain.value for domain in ReviewDomain}
    if (len(set(selected_reviewers)) != len(selected_reviewers)
            or any(reviewer not in allowed_reviewers for reviewer in selected_reviewers)):
        raise FinalizeReviewError("Invalid or duplicate selected reviewers.")
    if not all(char.isalnum() or char in "-_" for char in pr_id):
        raise FinalizeReviewError("Invalid PR identifier.")

    findings_directory = (
        reports_root
        / "findings"
        / pr_id
    )

    findings = load_findings(
        findings_directory=(
            findings_directory
        ),
        selected_reviewers=(
            selected_reviewers
        ),
    )

    pull_request = (
        rebuild_pull_request(
            plan
        )
    )

    context = rebuild_context(
        plan
    )

    workspace_path = Path(
        plan["workspace_path"]
    )

    if not workspace_path.exists():
        raise FinalizeReviewError(
            
                "Workspace no longer exists: "
                f"{workspace_path}"
            
        )

    verification_started = time.perf_counter()
    verification_directory = reports_root / "verification" / pr_id
    verification_path = verification_directory / "verification-results.json"
    verifications = []
    if verification_path.exists():
        require_valid_artifact(verification_path, "verification.schema.json")
        existing = read_json(verification_path)
        if existing["pr_id"] != pr_id:
            raise FinalizeReviewError("Verification PR identifier mismatch.")
        known_ids = {finding.id for finding in findings}
        seen_ids = set()
        for item in existing["results"]:
            finding_id = item["finding_id"]
            if finding_id not in known_ids or finding_id in seen_ids:
                raise FinalizeReviewError(f"Unknown or duplicate verification ID: {finding_id}")
            seen_ids.add(finding_id)
            verifications.append(VerificationResult.from_dict(item))
    completed_ids = {result.finding_id for result in verifications}
    verifier = DefaultFindingVerifier(reports_root=reports_root)
    verifications.extend(verifier.verify(
        pull_request=pull_request, context=context,
        repository_path=workspace_path.resolve(),
        findings=[finding for finding in findings if finding.id not in completed_ids],
    ))
    write_json(verification_path, {
        "pr_id": pr_id,
        "results": [result.to_dict() for result in verifications],
    })
    verification_duration = time.perf_counter() - verification_started

    metrics = ReviewMetrics(
        files_changed=(
            pull_request
            .changed_files_count
        ),
        files_analyzed=(
            pull_request
            .changed_files_count
        ),
        lines_added=(
            pull_request.additions
        ),
        lines_removed=(
            pull_request.deletions
        ),
        reviewers_selected=len(
            selected_reviewers
        ),
        reviewers_executed=len(
            selected_reviewers
        ),
        initial_findings=len(
            findings
        ),
        verified_findings=sum(
            1
            for result in verifications
            if (
                result.status
                == VerificationStatus.VERIFIED
            )
        ),
        refuted_findings=sum(
            1
            for result in verifications
            if (
                result.status
                == VerificationStatus.REFUTED
            )
        ),
        unverified_findings=sum(
            1
            for result in verifications
            if (
                result.status
                == VerificationStatus.UNVERIFIED
            )
        ),
    )

    metrics.verification_duration_seconds = verification_duration
    metrics.generated_tests = len({result.test_file for result in verifications if result.test_file})
    for result in verifications:
        summary = result.metadata.get("test_summary", {})
        metrics.tests_passed += summary.get("passed", 0)
        metrics.tests_failed += summary.get("failed", 0)
        metrics.tests_executed += sum(summary.get(key, 0) for key in ("passed", "failed", "errors", "skipped", "xfailed", "xpassed"))
    metrics.extra["reviewers_available"] = 7
    metrics.extra["reviewers_skipped"] = 7 - len(selected_reviewers)

    synthesizer = (
        DefaultReviewSynthesizer()
    )

    review = synthesizer.synthesize(
        pull_request=pull_request,
        context=context,
        findings=findings,
        verifications=verifications,
        reviewers_executed=(
            selected_reviewers
        ),
        metrics=metrics,
    )

    metrics.analysis_duration_seconds = time.perf_counter() - started
    review.metrics = metrics.to_dict()

    review_directory = (
        reports_root
        / "reviews"
        / pr_id
    )

    write_json(
        review_directory
        / "review.json",
        review.to_dict(),
    )

    write_text(
        review_directory
        / "review.md",
        render_review_markdown(
            review
        ),
    )

    write_json(
        reports_root
        / "metrics"
        / f"{pr_id}-finalize.json",
        metrics.to_dict(),
    )

    return {
        "success": True,
        "pr_id": pr_id,
        "reviewers_executed": (
            selected_reviewers
        ),
        "initial_findings": (
            metrics.initial_findings
        ),
        "verified_findings": (
            metrics.verified_findings
        ),
        "refuted_findings": (
            metrics.refuted_findings
        ),
        "final_findings": (
            metrics.final_findings
        ),
        "blocking_findings": (
            metrics.blocking_findings
        ),
        "review_json": str(
            review_directory
            / "review.json"
        ),
        "review_markdown": str(
            review_directory
            / "review.md"
        ),
        "verification_results": str(
            verification_directory
            / "verification-results.json"
        ),
    }

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
    description=(
    "Finalize a PR Guardian review "
    "after IBM Bob specialist reviewers complete."
    )
    )

    parser.add_argument(
        "pr_id",
        help=(
            "PR Guardian identifier returned by "
            "scripts/prepare_review.py"
        ),
    )

    parser.add_argument(
        "--reports-root",
        default=os.getenv(
            "PR_GUARDIAN_REPORTS",
            "reports",
        ),
    )

    return parser

def main() -> int:
    parser = build_parser()

    args = parser.parse_args()

    try:
        result = finalize_review(
            pr_id=args.pr_id,
            reports_root=Path(
                args.reports_root
            ),
        )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": str(exc),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )

        return 1

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0

if __name__ == "__main__":
    raise SystemExit(
    main()
    )
