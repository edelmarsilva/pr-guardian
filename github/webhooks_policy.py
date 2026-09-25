from __future__ import annotations

DEFAULT_PULL_REQUEST_ACTIONS = frozenset(
    {
        "opened",
        "reopened",
        "synchronize",
        "ready_for_review",
    }
)


def should_analyze_pull_request(
    action: str,
    *,
    allowed_actions: set[str] | frozenset[str] = (
        DEFAULT_PULL_REQUEST_ACTIONS
    ),
) -> bool:
    """
    Decide whether a pull_request webhook should trigger analysis.
    """

    return action in allowed_actions
