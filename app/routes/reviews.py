from __future__ import annotations

import json
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
)

reviews_bp = Blueprint(
    "reviews",
    __name__,
)


@reviews_bp.get("/<pr_id>")
def review_detail(
    pr_id: str,
):
    if not _is_safe_pr_id(
        pr_id
    ):
        abort(400)

    reports_root = Path(
        current_app.config[
            "PR_GUARDIAN_REPORTS"
        ]
    )

    review_path = (
        reports_root
        / "reviews"
        / pr_id
        / "review.json"
    )

    verification_path = (
        reports_root
        / "verification"
        / pr_id
        / "verification-results.json"
    )

    routing_path = (
        reports_root
        / "raw"
        / pr_id
        / "routing.json"
    )

    metrics_path = (
        reports_root
        / "metrics"
        / f"{pr_id}-orchestrator.json"
    )

    if not review_path.exists():
        abort(404)

    review = _read_json(
        review_path
    )

    verification = _read_json_optional(
        verification_path
    )

    routing = _read_json_optional(
        routing_path
    )

    if not metrics_path.exists():
        metrics_path = reports_root / "metrics" / f"{pr_id}-finalize.json"
    metrics = _read_json_optional(metrics_path)

    return render_template(
        "review.html",
        pr_id=pr_id,
        review=review,
        verification=verification,
        routing=routing,
        metrics=metrics,
    )


def _read_json(
    path: Path,
) -> dict:
    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        abort(500)


def _read_json_optional(
    path: Path,
) -> dict:
    if not path.exists():
        return {}

    return _read_json(
        path
    )


def _is_safe_pr_id(
    pr_id: str,
) -> bool:
    if not pr_id:
        return False

    allowed = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789-_"
    )

    return all(
        character in allowed
        for character in pr_id
    )
