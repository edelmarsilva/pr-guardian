from __future__ import annotations

from dataclasses import dataclass

@dataclass(slots=True)
class GitHubUser:
    login: str

@dataclass(slots=True)
class GitHubCommit:
    sha: str
    message: str
    author: str | None = None

@dataclass(slots=True)
class GitHubChangedFile:
    filename: str
    status: str

    additions: int
    deletions: int
    changes: int

    patch: str | None = None
    previous_filename: str | None = None

@dataclass(slots=True)
class GitHubPullRequestData:
    number: int

    title: str
    body: str | None

    author: str | None

    base_branch: str
    head_branch: str

    base_sha: str
    head_sha: str

    additions: int
    deletions: int
    changed_files: int
    commits: int

    html_url: str | None
