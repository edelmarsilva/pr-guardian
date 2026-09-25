from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)

from app.services.review_service import (
    ReviewService,
    ReviewServiceError,
)
from github import (
    GitHubWebhookService,
    InvalidWebhookSignature,
)

webhooks_bp = Blueprint(
    "webhooks",
    __name__,
)


@webhooks_bp.post("/github")
def github_webhook():
    secret = current_app.config.get(
        "GITHUB_WEBHOOK_SECRET"
    )

    if not secret:
        return (
            jsonify(
                {
                    "error": (
                        "GitHub webhook integration "
                        "is not configured."
                    )
                }
            ),
            503,
        )

    payload_body = request.get_data(
        cache=True,
        as_text=False,
    )

    signature_header = request.headers.get(
        "X-Hub-Signature-256"
    )

    event_header = request.headers.get(
        "X-GitHub-Event"
    )

    delivery_id = request.headers.get(
        "X-GitHub-Delivery"
    )

    webhook_service = (
        GitHubWebhookService(
            secret=secret
        )
    )

    try:
        result = webhook_service.process(
            payload_body=payload_body,
            signature_header=signature_header,
            event_header=event_header,
            delivery_id=delivery_id,
        )

    except InvalidWebhookSignature:
        return (
            jsonify(
                {
                    "error": (
                        "Invalid webhook signature."
                    )
                }
            ),
            401,
        )

    except Exception as exc:
        current_app.logger.exception(
            "Unable to process GitHub webhook."
        )

        return (
            jsonify(
                {
                    "error": (
                        "Unable to process webhook."
                    ),
                    "details": str(exc),
                }
            ),
            400,
        )

    if not result.accepted:
        return (
            jsonify(
                {
                    "accepted": False,
                    "reason": result.reason,
                    "delivery_id": delivery_id,
                }
            ),
            202,
        )

    pull_request = result.pull_request

    if pull_request is None:
        return (
            jsonify(
                {
                    "accepted": False,
                    "reason": (
                        "No Pull Request context "
                        "was produced."
                    ),
                }
            ),
            202,
        )

    review_service = ReviewService()

    try:
        analysis = review_service.analyze(
            owner=pull_request.owner,
            repository=(
                pull_request.repository
            ),
            pull_number=(
                pull_request.pull_number
            ),
        )

    except ReviewServiceError as exc:
        current_app.logger.exception(
            "PR Guardian analysis failed "
            "for webhook delivery %s.",
            delivery_id,
        )

        return (
            jsonify(
                {
                    "accepted": True,
                    "analysis_started": True,
                    "analysis_completed": False,
                    "delivery_id": delivery_id,
                    "error": str(exc),
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "accepted": True,
                "analysis_started": True,
                "analysis_completed": True,
                "delivery_id": delivery_id,
                "pr_id": (
                    analysis
                    .pull_request
                    .identifier
                ),
                "pull_request": (
                    analysis
                    .pull_request
                    .number
                ),
            }
        ),
        200,
    )
