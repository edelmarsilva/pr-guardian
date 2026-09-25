from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class RepositoryFileError(RuntimeError):
    """Raised when a repository file cannot be accessed safely."""

@dataclass(slots=True)
class RepositoryFile:
    relative_path: str
    absolute_path: Path

    size_bytes: int
    extension: str

    content: str | None = None

def resolve_repository_file(
    repository_path: Path,
    relative_path: str,
    ) -> Path:
    """
    Resolve a path while preventing directory traversal outside the repository.
    """

    repository_root = repository_path.resolve()

    candidate = (
        repository_root
        / relative_path
    ).resolve()

    try:
        candidate.relative_to(repository_root)
    except ValueError as exc:
        raise RepositoryFileError(
            f"Path escapes repository root: {relative_path}"
        ) from exc

    return candidate

def read_text_file(
    repository_path: Path,
    relative_path: str,
    *,
    max_size_bytes: int = 1_000_000,
    ) -> RepositoryFile:
    path = resolve_repository_file(
    repository_path,
    relative_path,
    )

    if not path.exists():
        raise RepositoryFileError(
            f"File does not exist: {relative_path}"
        )

    if not path.is_file():
        raise RepositoryFileError(
            f"Path is not a file: {relative_path}"
        )

    size = path.stat().st_size

    if size > max_size_bytes:
        return RepositoryFile(
            relative_path=relative_path,
            absolute_path=path,
            size_bytes=size,
            extension=path.suffix.lower(),
            content=None,
        )

    try:
        content = path.read_text(
            encoding="utf-8",
        )
    except UnicodeDecodeError:
        content = None

    return RepositoryFile(
        relative_path=relative_path,
        absolute_path=path,
        size_bytes=size,
        extension=path.suffix.lower(),
        content=content,
    )

def list_repository_files(
    repository_path: Path,
    *,
    excluded_directories: set[str] | None = None,
    ) -> list[str]:
    excluded = excluded_directories or {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    }

    root = repository_path.resolve()

    results: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(root)

        if any(
            part in excluded
            for part in relative.parts
        ):
            continue

        results.append(
            relative.as_posix()
        )

    return sorted(results)

def find_files_by_name(
    repository_path: Path,
    names: set[str],
    ) -> list[str]:
    return [
    path
    for path in list_repository_files(repository_path)
    if Path(path).name in names
    ]

def find_files_by_extension(
    repository_path: Path,
    extensions: set[str],
    ) -> list[str]:
    normalized = {
    extension.lower()
    if extension.startswith(".")
    else f".{extension.lower()}"
    for extension in extensions
    }

    return [
        path
        for path in list_repository_files(repository_path)
        if Path(path).suffix.lower() in normalized
    ]
