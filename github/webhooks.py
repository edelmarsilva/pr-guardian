from **future** import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

class GitHubWebhookError(RuntimeError):
"""Raised when a GitHub webhook cannot be validated or parsed."""

class InvalidWebhookSignature(GitHubWebhookError):
"""Raised when the webhook signature is invalid."""

class UnsupportedWebhookEvent(GitHubWebhookError):
"""Raised when the webhook event is not supported."""

@dataclass(slots=True)
class GitHubWebhookEvent:
event: str
delivery_id: str | None
action: str | None

```
payload: dict[str, Any]
```

@dataclass(slots=True)
class PullRequestWebhook:
action: str

```
owner: str
repository: str

pull_number: int

base_sha: str
head_sha: str

base_branch: str
head_branch: str

sender: str | None = None
installation_id: int | None = None

delivery_id: str | None = None
```

def verify_webhook_signature(
payload_body: bytes,
signature_header: str | None,
secret: str,
) -> None:
"""
Validate GitHub's X-Hub-Signature-256 header.

```
GitHub signs the exact request body using HMAC-SHA256.
"""

if not signature_header:
    raise InvalidWebhookSignature(
        "Missing X-Hub-Signature-256 header."
    )

if not signature_header.startswith("sha256="):
    raise InvalidWebhookSignature(
        "Unsupported webhook signature format."
    )

expected_signature = (
    "sha256="
    + hmac.new(
        secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
)

if not hmac.compare_digest(
    expected_signature,
    signature_header,
):
    raise InvalidWebhookSignature(
        "Webhook signature does not match."
    )
```

def parse_webhook_event(
*,
event_header: str | None,
delivery_id: str | None,
payload_body: bytes,
) -> GitHubWebhookEvent:
if not event_header:
raise GitHubWebhookError(
"Missing X-GitHub-Event header."
)

```
try:
    payload = json.loads(
        payload_body.decode("utf-8")
    )
except (UnicodeDecodeError, json.JSONDecodeError) as exc:
    raise GitHubWebhookError(
        "Invalid webhook JSON payload."
    ) from exc

if not isinstance(payload, dict):
    raise GitHubWebhookError(
        "Webhook payload must be a JSON object."
    )

return GitHubWebhookEvent(
    event=event_header,
    delivery_id=delivery_id,
    action=payload.get("action"),
    payload=payload,
)
```

def parse_pull_request_webhook(
event: GitHubWebhookEvent,
) -> PullRequestWebhook:
if event.event != "pull_request":
raise UnsupportedWebhookEvent(
f"Unsupported event: {event.event}"
)

```
payload = event.payload

pull_request = payload.get("pull_request")
repository = payload.get("repository")

if not isinstance(pull_request, dict):
    raise GitHubWebhookError(
        "Missing pull_request payload."
    )

if not isinstance(repository, dict):
    raise GitHubWebhookError(
        "Missing repository payload."
    )

owner_data = repository.get("owner") or {}

base = pull_request.get("base") or {}
head = pull_request.get("head") or {}

sender_data = payload.get("sender") or {}
installation_data = payload.get("installation") or {}

owner = (
    owner_data.get("login")
    or owner_data.get("name")
)

repository_name = repository.get("name")

if not owner or not repository_name:
    raise GitHubWebhookError(
        "Repository identity is incomplete."
    )

return PullRequestWebhook(
    action=str(
        payload.get("action", "")
    ),
    owner=str(owner),
    repository=str(repository_name),
    pull_number=int(
        pull_request["number"]
    ),
    base_sha=str(
        base.get("sha", "")
    ),
    head_sha=str(
        head.get("sha", "")
    ),
    base_branch=str(
        base.get("ref", "")
    ),
    head_branch=str(
        head.get("ref", "")
    ),
    sender=sender_data.get("login"),
    installation_id=installation_data.get("id"),
    delivery_id=event.delivery_id,
)
```