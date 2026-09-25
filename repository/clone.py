from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class RepositoryError(RuntimeError):
    """Raised when a repository operation fails."""

@dataclass(slots=True)
class RepositoryWorkspace:
    path: Path
    remote_url: str
    base_sha: str | None = None
    head_sha: str | None = None

def _run_git(
    args: list[str],
    cwd: Path | None = None,
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

def clone_repository(
    remote_url: str,
    destination: Path,
    *,
    depth: int | None = None,
    ) -> RepositoryWorkspace:
    """
    Clone a repository into a dedicated workspace.

    The destination is replaced if it already exists.
    """

    if destination.exists():
        shutil.rmtree(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args = ["clone"]

    if depth is not None:
        args.extend(["--depth", str(depth)])

    args.extend(
        [
            remote_url,
            str(destination),
        ]
    )

    _run_git(args)

    return RepositoryWorkspace(
        path=destination,
        remote_url=remote_url,
    )

def fetch_repository(
    workspace: RepositoryWorkspace,
    ) -> None:
    _run_git(
    ["fetch", "--all", "--tags", "--prune"],
    cwd=workspace.path,
    )

def checkout_commit(
    workspace: RepositoryWorkspace,
    commit_sha: str,
    ) -> None:
    _run_git(
    ["checkout", "--detach", commit_sha],
    cwd=workspace.path,
    )

def checkout_branch(
    workspace: RepositoryWorkspace,
    branch: str,
    ) -> None:
    _run_git(
    ["checkout", branch],
    cwd=workspace.path,
    )

def ensure_commit_available(
    workspace: RepositoryWorkspace,
    commit_sha: str,
    ) -> None:
    try:
        _run_git(
        ["cat-file", "-e", f"{commit_sha}^{{commit}}"],
        cwd=workspace.path,
        )
        return
    except RepositoryError:
        pass

        _run_git(
            ["fetch", "origin", commit_sha],
            cwd=workspace.path,
        )

def prepare_pull_request_workspace(
    remote_url: str,
    destination: Path,
    *,
    base_sha: str,
    head_sha: str,
    ) -> RepositoryWorkspace:
    """
    Clone and prepare a repository workspace for PR analysis.

    The repository is checked out at the PR head commit while preserving
    both base and head commit identifiers for diff analysis.
    """

    workspace = clone_repository(
        remote_url,
        destination,
    )

    ensure_commit_available(
        workspace,
        base_sha,
    )

    ensure_commit_available(
        workspace,
        head_sha,
    )

    checkout_commit(
        workspace,
        head_sha,
    )

    workspace.base_sha = base_sha
    workspace.head_sha = head_sha

    return workspace
