from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from github import (
    GitHubClient,
    GitHubReviewService,
    PullRequestService,
    )
from github.review_mapper import (
    build_github_review_payload,
    )
from models import Finding, Review


class PublishReviewError(RuntimeError):
    """Raised when a review cannot be published safely."""


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
        raise PublishReviewError(
            f"File does not exist: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise PublishReviewError(
            f"Invalid JSON file: {path}"
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise PublishReviewError(
            f"Expected JSON object in {path}"
        )

    return payload


def rebuild_review(
    payload: dict[str, Any],
    ) -> Review:
    raw_findings = payload.get(
        "findings",
        [],
    )

    if not isinstance(
        raw_findings,
        list,
    ):
        raise PublishReviewError(
            "Review findings must be a list."
        )

    findings = [
        Finding.from_dict(
            item
        )
        for item
        in raw_findings
        if isinstance(
            item,
            dict,
        )
    ]

    return Review(
        pr_id=str(
            payload["pr_id"]
        ),
        summary=str(
            payload.get(
                "summary",
                "",
            )
        ),
        findings=findings,
        reviewers_executed=list(
            payload.get(
                "reviewers_executed",
                [],
            )
        ),
        metrics=dict(
            payload.get(
                "metrics",
                {},
            )
        ),
        metadata=dict(
            payload.get(
                "metadata",
                {},
            )
        ),
    )


def parse_repository(
    value: str,
    ) -> tuple[str, str]:
    if "/" not in value:
        raise PublishReviewError(
            
                "Repository must use "
                "owner/repository format."
            
        )

    owner, repository = (
        value.split(
            "/",
            1,
        )
    )

    if not owner or not repository:
        raise PublishReviewError(
            "Invalid repository value."
        )

    return (
        owner,
        repository,
    )


def publish_review(
    *,
    repository: str,
    pull_number: int,
    review_path: Path,
    event: str,
    dry_run: bool,
    ) -> dict[str, Any]:
    token = os.getenv(
        "GITHUB_TOKEN"
    )

    if not token:
        raise PublishReviewError(
            
                "GITHUB_TOKEN is required "
                "to publish a review."
            
        )

    owner, repository_name = (
        parse_repository(
            repository
        )
    )

    review_payload = read_json(
        review_path
    )

    review = rebuild_review(
        review_payload
    )

    client = GitHubClient(
        token=token
    )

    pull_service = (
        PullRequestService(
            client
        )
    )

    pull_request = (
        pull_service.get_pull_request(
            owner=owner,
            repository=(
                repository_name
            ),
            number=pull_number,
        )
    )

    if review.pr_id != pull_request.identifier:
        raise PublishReviewError("Review belongs to a different Pull Request.")
    reviewed_head = review.metadata.get("head_sha")
    if not reviewed_head or reviewed_head != pull_request.head_sha:
        raise PublishReviewError(
            "Review head SHA is missing or stale; prepare and finalize the current head."
        )

    payload = (
        build_github_review_payload(
            review,
            changed_files=(
                pull_request
                .changed_files
            ),
            commit_id=(
                pull_request
                .head_sha
            ),
            event=event,
        )
    )

    publishable_findings = (
        review.publishable_findings()
    )

    result = {
        "repository": (
            repository
        ),
        "pull_number": (
            pull_number
        ),
        "commit_id": (
            pull_request.head_sha
        ),
        "event": (
            event
        ),
        "publishable_findings": (
            len(
                publishable_findings
            )
        ),
        "inline_comments": (
            len(
                payload.comments
            )
        ),
        "summary_only_findings": (
            len(
                publishable_findings
            )
            - len(
                payload.comments
            )
        ),
        "dry_run": (
            dry_run
        ),
    }

    if dry_run:
        result[
            "payload"
        ] = {
            "body": (
                payload.body
            ),
            "event": (
                payload.event
            ),
            "commit_id": (
                payload.commit_id
            ),
            "comments": [
                {
                    "path": (
                        comment.path
                    ),
                    "line": (
                        comment.line
                    ),
                    "body": (
                        comment.body
                    ),
                }
                for comment
                in payload.comments
            ],
        }

        return result

    review_service = (
        GitHubReviewService(
            client
        )
    )

    response = (
        review_service.create_review(
            owner=owner,
            repository=(
                repository_name
            ),
            pull_number=(
                pull_number
            ),
            payload=payload,
        )
    )

    result.update(
        {
            "published": True,
            "github_review_id": (
                response.get(
                    "id"
                )
            ),
            "github_review_url": (
                response.get(
                    "html_url"
                )
            ),
            "github_review_state": (
                response.get(
                    "state"
                )
            ),
        }
    )

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Publish a finalized "
            "PR Guardian review to GitHub."
        )
    )

    parser.add_argument(
        "repository",
        help=(
            "GitHub repository in "
            "owner/repository format."
        ),
    )

    parser.add_argument(
        "pull_number",
        type=int,
        help=(
            "GitHub Pull Request number."
        ),
    )

    parser.add_argument(
        "--review",
        required=True,
        help=(
            "Path to finalized "
            "review.json."
        ),
    )

    parser.add_argument(
        "--event",
        choices=[
            "COMMENT",
            "APPROVE",
            "REQUEST_CHANGES",
        ],
        default="COMMENT",
        help=(
            "GitHub review event."
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Build and validate the "
            "GitHub payload without "
            "publishing it."
        ),
    )

    return parser


def main() -> int:
    parser = build_parser()

    args = parser.parse_args()

    try:
        result = publish_review(
            repository=(
                args.repository
            ),
            pull_number=(
                args.pull_number
            ),
            review_path=Path(
                args.review
            ),
            event=args.event,
            dry_run=(
                args.dry_run
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
            {
                "success": True,
                **result,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
