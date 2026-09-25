from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from github import (
    GitHubWebhookService,
    InvalidWebhookSignature,
)

SECRET = "super-secret-test-key"


def sign_payload(
    payload: bytes,
    secret: str = SECRET,
) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def make_pull_request_payload(
    *,
    action: str = "opened",
) -> bytes:
    payload = {
        "action": action,
        "number": 42,
        "repository": {
            "name": "project",
            "full_name": "example/project",
            "owner": {
                "login": "example",
            },
        },
        "pull_request": {
            "number": 42,
            "title": "Synthetic Pull Request",
            "body": "Test PR",
            "state": "open",
            "user": {
                "login": "alice",
            },
            "base": {
                "ref": "main",
                "sha": "base123",
            },
            "head": {
                "ref": "feature/test",
                "sha": "head456",
            },
            "html_url": (
                "https://github.com/"
                "example/project/pull/42"
            ),
        },
    }

    return json.dumps(
        payload
    ).encode("utf-8")


def test_valid_signature_is_accepted():
    payload = make_pull_request_payload()

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="pull_request",
        delivery_id="delivery-001",
    )

    assert result.accepted is True


def test_invalid_signature_is_rejected():
    payload = make_pull_request_payload()

    service = GitHubWebhookService(
        secret=SECRET
    )

    with pytest.raises(
        InvalidWebhookSignature
    ):
        service.process(
            payload_body=payload,
            signature_header=(
                "sha256=invalid"
            ),
            event_header="pull_request",
            delivery_id="delivery-002",
        )


def test_missing_signature_is_rejected():
    payload = make_pull_request_payload()

    service = GitHubWebhookService(
        secret=SECRET
    )

    with pytest.raises(
        InvalidWebhookSignature
    ):
        service.process(
            payload_body=payload,
            signature_header=None,
            event_header="pull_request",
            delivery_id="delivery-003",
        )


def test_opened_pull_request_is_accepted():
    payload = make_pull_request_payload(
        action="opened"
    )

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="pull_request",
        delivery_id="delivery-004",
    )

    assert result.accepted is True

    assert (
        result.pull_request
        is not None
    )

    assert (
        result.pull_request.owner
        == "example"
    )

    assert (
        result.pull_request.repository
        == "project"
    )

    assert (
        result.pull_request.pull_number
        == 42
    )


def test_synchronize_pull_request_is_accepted():
    payload = make_pull_request_payload(
        action="synchronize"
    )

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="pull_request",
        delivery_id="delivery-005",
    )

    assert result.accepted is True


def test_reopened_pull_request_is_accepted():
    payload = make_pull_request_payload(
        action="reopened"
    )

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="pull_request",
        delivery_id="delivery-006",
    )

    assert result.accepted is True


def test_ready_for_review_pull_request_is_accepted():
    payload = make_pull_request_payload(
        action="ready_for_review"
    )

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="pull_request",
        delivery_id="delivery-007",
    )

    assert result.accepted is True


@pytest.mark.parametrize(
    "action",
    [
        "closed",
        "assigned",
        "unassigned",
        "labeled",
        "unlabeled",
        "locked",
        "unlocked",
    ],
)
def test_irrelevant_pull_request_actions_are_ignored(
    action: str,
):
    payload = make_pull_request_payload(
        action=action
    )

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="pull_request",
        delivery_id=(
            f"delivery-{action}"
        ),
    )

    assert result.accepted is False


def test_ping_event_does_not_trigger_review():
    payload = json.dumps(
        {
            "zen": "Keep it logically awesome.",
            "hook_id": 123,
        }
    ).encode("utf-8")

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="ping",
        delivery_id="delivery-ping",
    )

    assert result.accepted is False


def test_non_pull_request_event_is_ignored():
    payload = json.dumps(
        {
            "ref": "refs/heads/main",
        }
    ).encode("utf-8")

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="push",
        delivery_id="delivery-push",
    )

    assert result.accepted is False


def test_invalid_json_payload_is_rejected():
    payload = b"{invalid-json"

    service = GitHubWebhookService(
        secret=SECRET
    )

    with pytest.raises(
        ValueError
    ):
        service.process(
            payload_body=payload,
            signature_header=sign_payload(
                payload
            ),
            event_header="pull_request",
            delivery_id="delivery-invalid",
        )


def test_signature_is_calculated_over_raw_payload_bytes():
    original_payload = (
        b'{"action":"opened","number":42}'
    )

    modified_payload = (
        b'{"action": "opened", "number": 42}'
    )

    service = GitHubWebhookService(
        secret=SECRET
    )

    signature = sign_payload(
        original_payload
    )

    with pytest.raises(
        InvalidWebhookSignature
    ):
        service.process(
            payload_body=modified_payload,
            signature_header=signature,
            event_header="pull_request",
            delivery_id="delivery-bytes",
        )


def test_pull_request_context_preserves_repository_identity():
    payload = make_pull_request_payload()

    service = GitHubWebhookService(
        secret=SECRET
    )

    result = service.process(
        payload_body=payload,
        signature_header=sign_payload(
            payload
        ),
        event_header="pull_request",
        delivery_id="delivery-identity",
    )

    pull_request = result.pull_request

    assert pull_request is not None

    assert (
        pull_request.owner
        == "example"
    )

    assert (
        pull_request.repository
        == "project"
    )

    assert (
        pull_request.pull_number
        == 42
    )
