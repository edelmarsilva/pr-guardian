from **future** import annotations

from dataclasses import dataclass
from typing import Any

import requests

class GitHubAPIError(RuntimeError):
"""Raised when a GitHub API request fails."""

@dataclass(slots=True)
class GitHubResponse:
data: Any
status_code: int
headers: dict[str, str]

class GitHubClient:
"""
Minimal GitHub REST API client used by PR Guardian.

```
This class is intentionally generic. Pull Request-specific
behavior belongs in github.pull_requests.
"""

BASE_URL = "https://api.github.com"

def __init__(
    self,
    token: str | None = None,
    *,
    timeout: float = 30.0,
    api_version: str | None = None,
) -> None:
    self.token = token
    self.timeout = timeout
    self.api_version = api_version

    self.session = requests.Session()

    self.session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "User-Agent": "PR-Guardian",
        }
    )

    if token:
        self.session.headers["Authorization"] = f"Bearer {token}"

    if api_version:
        self.session.headers["X-GitHub-Api-Version"] = api_version

def _request(
    self,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> GitHubResponse:
    url = f"{self.BASE_URL}{path}"

    try:
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            timeout=self.timeout,
        )
    except requests.RequestException as exc:
        raise GitHubAPIError(
            f"GitHub request failed: {exc}"
        ) from exc

    if not response.ok:
        self._raise_api_error(
            method=method,
            url=url,
            response=response,
        )

    if response.status_code == 204:
        data: Any = None
    else:
        try:
            data = response.json()
        except ValueError:
            data = response.text

    return GitHubResponse(
        data=data,
        status_code=response.status_code,
        headers=dict(response.headers),
    )

def get(
    self,
    path: str,
    *,
    params: dict[str, Any] | None = None,
) -> GitHubResponse:
    return self._request(
        "GET",
        path,
        params=params,
    )

def post(
    self,
    path: str,
    *,
    json: dict[str, Any] | None = None,
) -> GitHubResponse:
    return self._request(
        "POST",
        path,
        json=json,
    )

def paginate(
    self,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    per_page: int = 100,
    max_pages: int = 100,
) -> list[Any]:
    """
    Retrieve paginated GitHub REST API resources.

    Stops when a page returns fewer than `per_page` items.

    max_pages prevents accidental unbounded API traversal.
    """

    items: list[Any] = []

    base_params = dict(params or {})
    base_params["per_page"] = per_page

    for page in range(1, max_pages + 1):
        page_params = {
            **base_params,
            "page": page,
        }

        response = self.get(
            path,
            params=page_params,
        )

        data = response.data

        if not isinstance(data, list):
            raise GitHubAPIError(
                f"Expected list response from {path}"
            )

        items.extend(data)

        if len(data) < per_page:
            break

    return items

@staticmethod
def _raise_api_error(
    *,
    method: str,
    url: str,
    response: requests.Response,
) -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = response.text

    rate_limit_remaining = response.headers.get(
        "X-RateLimit-Remaining"
    )

    rate_limit_reset = response.headers.get(
        "X-RateLimit-Reset"
    )

    message = (
        f"GitHub API returned HTTP {response.status_code} "
        f"for {method} {url}. "
        f"Response: {payload}"
    )

    if rate_limit_remaining == "0":
        message += (
            f" Rate limit exhausted."
            f" Reset: {rate_limit_reset}."
        )

    raise GitHubAPIError(message)
```