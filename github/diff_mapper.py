from __future__ import annotations

import re
from dataclasses import dataclass


HUNK_HEADER = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


@dataclass(slots=True)
class DiffLine:
    patch_position: int
    kind: str
    old_line: int | None
    new_line: int | None
    content: str

    @property
    def is_commentable_new_line(self) -> bool:
        return (
            self.kind in {"context", "addition"}
            and self.new_line is not None
        )


@dataclass(slots=True)
class DiffMap:
    filename: str
    lines: list[DiffLine]

    def find_new_line(
        self,
        line_number: int,
    ) -> DiffLine | None:
        for line in self.lines:
            if (
                line.new_line
                == line_number
                and line.is_commentable_new_line
            ):
                return line

        return None

    def contains_new_line(
        self,
        line_number: int,
    ) -> bool:
        return (
            self.find_new_line(
                line_number
            )
            is not None
        )

    def commentable_lines(
        self,
    ) -> set[int]:
        return {
            line.new_line
            for line in self.lines
            if (
                line.is_commentable_new_line
                and line.new_line
                is not None
            )
        }


def parse_patch(
    *,
    filename: str,
    patch: str,
) -> DiffMap:
    """
    Parse a GitHub unified diff patch and map old/new line numbers.

    Only lines present in the patch can receive inline review comments.
    """

    lines: list[DiffLine] = []

    old_line: int | None = None
    new_line: int | None = None

    patch_position = 0
    inside_hunk = False

    for raw_line in patch.splitlines():
        hunk_match = HUNK_HEADER.match(
            raw_line
        )

        if hunk_match:
            old_line = int(
                hunk_match.group(
                    "old_start"
                )
            )

            new_line = int(
                hunk_match.group(
                    "new_start"
                )
            )

            inside_hunk = True

            continue

        if not inside_hunk:
            continue

        patch_position += 1

        if raw_line.startswith(
            "\\ No newline at end of file"
        ):
            continue

        if raw_line.startswith("+"):
            lines.append(
                DiffLine(
                    patch_position=(
                        patch_position
                    ),
                    kind="addition",
                    old_line=None,
                    new_line=new_line,
                    content=raw_line[1:],
                )
            )

            assert new_line is not None

            new_line += 1

            continue

        if raw_line.startswith("-"):
            lines.append(
                DiffLine(
                    patch_position=(
                        patch_position
                    ),
                    kind="deletion",
                    old_line=old_line,
                    new_line=None,
                    content=raw_line[1:],
                )
            )

            assert old_line is not None

            old_line += 1

            continue

        if raw_line.startswith(" "):
            lines.append(
                DiffLine(
                    patch_position=(
                        patch_position
                    ),
                    kind="context",
                    old_line=old_line,
                    new_line=new_line,
                    content=raw_line[1:],
                )
            )

            assert old_line is not None
            assert new_line is not None

            old_line += 1
            new_line += 1

            continue

        # Defensive handling for unexpected patch content.
        lines.append(
            DiffLine(
                patch_position=(
                    patch_position
                ),
                kind="unknown",
                old_line=None,
                new_line=None,
                content=raw_line,
            )
        )

    return DiffMap(
        filename=filename,
        lines=lines,
    )


def is_valid_inline_location(
    *,
    filename: str,
    line_number: int | None,
    patch: str | None,
) -> bool:
    if (
        line_number is None
        or line_number < 1
        or not patch
    ):
        return False

    diff_map = parse_patch(
        filename=filename,
        patch=patch,
    )

    return diff_map.contains_new_line(
        line_number
    )


def nearest_commentable_line(
    *,
    filename: str,
    requested_line: int,
    patch: str,
    max_distance: int = 3,
) -> int | None:
    """
    Find a nearby line present in the PR patch.

    This must not silently change the meaning of a finding.
    It is intended only for tightly nearby changed/context lines.
    """

    diff_map = parse_patch(
        filename=filename,
        patch=patch,
    )

    available = (
        diff_map.commentable_lines()
    )

    if requested_line in available:
        return requested_line

    candidates = [
        line
        for line in available
        if abs(
            line
            - requested_line
        )
        <= max_distance
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda line: abs(
            line
            - requested_line
        ),
    )