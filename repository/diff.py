from **future** import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .clone import RepositoryError

@dataclass(slots=True)
class DiffHunk:
old_start: int
old_count: int
new_start: int
new_count: int
header: str
lines: list[str] = field(default_factory=list)

@dataclass(slots=True)
class FileDiff:
filename: str
previous_filename: str | None = None
status: str = "modified"

```
additions: int = 0
deletions: int = 0

patch: str = ""

hunks: list[DiffHunk] = field(default_factory=list)
```

_HUNK_PATTERN = re.compile(
r"@@ -(?P<old_start>\d+)"
r"(?:,(?P<old_count>\d+))?"
r" +(?P<new_start>\d+)"
r"(?:,(?P<new_count>\d+))? @@"
)

def _run_git(
args: list[str],
cwd: Path,
) -> str:
command = ["git", *args]

```
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

return result.stdout
```

def get_raw_diff(
repository_path: Path,
base_sha: str,
head_sha: str,
) -> str:
return _run_git(
[
"diff",
"--no-ext-diff",
"--unified=3",
base_sha,
head_sha,
],
repository_path,
)

def get_changed_file_names(
repository_path: Path,
base_sha: str,
head_sha: str,
) -> list[str]:
output = _run_git(
[
"diff",
"--name-only",
base_sha,
head_sha,
],
repository_path,
)

```
return [
    line.strip()
    for line in output.splitlines()
    if line.strip()
]
```

def get_name_status(
repository_path: Path,
base_sha: str,
head_sha: str,
) -> list[tuple[str, str, str | None]]:
"""
Return tuples in the form:
(status, filename, previous_filename)
"""

```
output = _run_git(
    [
        "diff",
        "--name-status",
        "-M",
        base_sha,
        head_sha,
    ],
    repository_path,
)

results: list[tuple[str, str, str | None]] = []

for line in output.splitlines():
    parts = line.split("\t")

    if not parts:
        continue

    status_code = parts[0]

    if status_code.startswith("R") and len(parts) >= 3:
        results.append(
            (
                "renamed",
                parts[2],
                parts[1],
            )
        )
        continue

    if len(parts) < 2:
        continue

    mapping = {
        "A": "added",
        "M": "modified",
        "D": "deleted",
        "C": "copied",
    }

    status = mapping.get(
        status_code[0],
        "modified",
    )

    results.append(
        (
            status,
            parts[1],
            None,
        )
    )

return results
```

def get_numstat(
repository_path: Path,
base_sha: str,
head_sha: str,
) -> dict[str, tuple[int, int]]:
output = _run_git(
[
"diff",
"--numstat",
base_sha,
head_sha,
],
repository_path,
)

```
stats: dict[str, tuple[int, int]] = {}

for line in output.splitlines():
    parts = line.split("\t")

    if len(parts) < 3:
        continue

    additions_raw = parts[0]
    deletions_raw = parts[1]
    filename = parts[2]

    additions = (
        int(additions_raw)
        if additions_raw.isdigit()
        else 0
    )

    deletions = (
        int(deletions_raw)
        if deletions_raw.isdigit()
        else 0
    )

    stats[filename] = (
        additions,
        deletions,
    )

return stats
```

def parse_hunks(
patch: str,
) -> list[DiffHunk]:
hunks: list[DiffHunk] = []

```
current: DiffHunk | None = None

for line in patch.splitlines():
    match = _HUNK_PATTERN.search(line)

    if match:
        current = DiffHunk(
            old_start=int(match.group("old_start")),
            old_count=int(match.group("old_count") or 1),
            new_start=int(match.group("new_start")),
            new_count=int(match.group("new_count") or 1),
            header=line,
        )

        hunks.append(current)
        continue

    if current is not None:
        current.lines.append(line)

return hunks
```