from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .clone import RepositoryError

@dataclass(slots=True)
class CommitInfo:
    sha: str
    author: str
    email: str
    date: str
    subject: str

def _run_git(
    args: list[str],
    cwd: Path,
    ) -> str:
    command = ["git", *args]

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RepositoryError(
            f"Git command failed: {' '.join(command)}\n"
            f"{result.stderr.strip()}"
        )

    return result.stdout.strip()

def get_file_history(
    repository_path: Path,
    relative_path: str,
    *,
    limit: int = 20,
    ) -> list[CommitInfo]:
    """
    Return recent commits affecting a file.
    """

    format_string = "%H%x1f%an%x1f%ae%x1f%aI%x1f%s"

    output = _run_git(
        [
            "log",
            f"-{limit}",
            f"--format={format_string}",
            "--follow",
            "--",
            relative_path,
        ],
        repository_path,
    )

    commits: list[CommitInfo] = []

    for line in output.splitlines():
        parts = line.split("\x1f")

        if len(parts) != 5:
            continue

        commits.append(
            CommitInfo(
                sha=parts[0],
                author=parts[1],
                email=parts[2],
                date=parts[3],
                subject=parts[4],
            )
        )

    return commits

def get_recent_repository_history(
    repository_path: Path,
    *,
    limit: int = 50,
    ) -> list[CommitInfo]:
    format_string = "%H%x1f%an%x1f%ae%x1f%aI%x1f%s"

    output = _run_git(
        [
            "log",
            f"-{limit}",
            f"--format={format_string}",
        ],
        repository_path,
    )

    commits: list[CommitInfo] = []

    for line in output.splitlines():
        parts = line.split("\x1f")

        if len(parts) != 5:
            continue

        commits.append(
            CommitInfo(
                sha=parts[0],
                author=parts[1],
                email=parts[2],
                date=parts[3],
                subject=parts[4],
            )
        )

    return commits

def get_blame(
    repository_path: Path,
    relative_path: str,
    *,
    start_line: int | None = None,
    end_line: int | None = None,
    ) -> str:
    args = [
    "blame",
    "--line-porcelain",
    ]

    if start_line is not None and end_line is not None:
        args.extend(
            [
                "-L",
                f"{start_line},{end_line}",
            ]
        )

    args.extend(
        [
            "--",
            relative_path,
        ]
    )

    return _run_git(
        args,
        repository_path,
    )
