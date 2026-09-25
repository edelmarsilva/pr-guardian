from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ChangedFile:
    filename: str
    status: str

    additions: int = 0
    deletions: int = 0
    changes: int = 0

    patch: str | None = None

    previous_filename: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PullRequest:
    repository_owner: str
    repository_name: str
    number: int

    title: str
    description: str | None

    base_branch: str
    head_branch: str

    base_sha: str
    head_sha: str

    author: str | None = None

    additions: int = 0
    deletions: int = 0
    changed_files_count: int = 0
    commit_count: int = 0

    changed_files: list[ChangedFile] = field(default_factory=list)

    commits: list[str] = field(default_factory=list)

    html_url: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def repository_full_name(self) -> str:
        return f"{self.repository_owner}/{self.repository_name}"

    @property
    def identifier(self) -> str:
        return f"{self.repository_owner}-{self.repository_name}-pr-{self.number}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository_owner": self.repository_owner,
            "repository_name": self.repository_name,
            "repository_full_name": self.repository_full_name,
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "base_branch": self.base_branch,
            "head_branch": self.head_branch,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "author": self.author,
            "additions": self.additions,
            "deletions": self.deletions,
            "changed_files_count": self.changed_files_count,
            "commit_count": self.commit_count,
            "changed_files": [
                {
                    "filename": item.filename,
                    "status": item.status,
                    "additions": item.additions,
                    "deletions": item.deletions,
                    "changes": item.changes,
                    "patch": item.patch,
                    "previous_filename": item.previous_filename,
                    "metadata": item.metadata,
                }
                for item in self.changed_files
            ],
            "commits": self.commits,
            "html_url": self.html_url,
            "metadata": self.metadata,
        }
