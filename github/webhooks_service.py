from **future** import annotations

from dataclasses import dataclass

from .webhook_policy import should_analyze_pull_request
from .webhooks import (
GitHubWebhookEvent,
PullRequestWebhook,
parse_pull_request_webhook,
parse_webhook_event,
verify_webhook_signature,
)

@dataclass(slots=True)
class WebhookProcessingResult:
accepted: bool
reason: str

```
event: GitHubWebhookEvent
pull_request: PullRequestWebhook | None = None
```

class GitHubWebhookService:
def **init**(
self,
secret: str,
) -> None:
if not secret:
raise ValueError(
"GitHub webhook secret must not be empty."
)

```
    self.secret = secret

def process(
    self,
    *,
    payload_body: bytes,
    signature_header: str | None,
    event_header: str | None,
    delivery_id: str | None,
) -> WebhookProcessingResult:
    verify_webhook_signature(
        payload_body,
        signature_header,
        self.secret,
    )

    event = parse_webhook_event(
        event_header=event_header,
        delivery_id=delivery_id,
        payload_body=payload_body,
    )

    if event.event == "ping":
        return WebhookProcessingResult(
            accepted=False,
            reason="GitHub ping event.",
            event=event,
        )

    if event.event != "pull_request":
        return WebhookProcessingResult(
            accepted=False,
            reason=(
                f"Event '{event.event}' is not "
                "configured for PR analysis."
            ),
            event=event,
        )

    pull_request = parse_pull_request_webhook(
        event
    )

    if not should_analyze_pull_request(
        pull_request.action
    ):
        return WebhookProcessingResult(
            accepted=False,
            reason=(
                f"Pull Request action "
                f"'{pull_request.action}' "
                "does not trigger analysis."
            ),
            event=event,
            pull_request=pull_request,
        )

    return WebhookProcessingResult(
        accepted=True,
        reason="Pull Request analysis requested.",
        event=event,
        pull_request=pull_request,
    )
```