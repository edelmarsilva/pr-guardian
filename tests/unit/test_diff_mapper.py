from __future__ import annotations

from github.diff_mapper import (
    is_valid_inline_location,
    nearest_commentable_line,
    parse_patch,
)

SIMPLE_PATCH = """@@ -10,3 +10,4 @@
 line one
-line two
+line two changed
+line three
 line four
"""


def test_parse_patch_maps_context_lines():
    diff_map = parse_patch(
        filename="app/service.py",
        patch=SIMPLE_PATCH,
    )

    line = diff_map.find_new_line(
        10
    )

    assert line is not None
    assert line.kind == "context"
    assert line.new_line == 10


def test_parse_patch_maps_added_lines():
    diff_map = parse_patch(
        filename="app/service.py",
        patch=SIMPLE_PATCH,
    )

    changed = diff_map.find_new_line(
        11
    )

    added = diff_map.find_new_line(
        12
    )

    assert changed is not None
    assert changed.kind == "addition"

    assert added is not None
    assert added.kind == "addition"


def test_deleted_line_is_not_commentable_on_new_side():
    diff_map = parse_patch(
        filename="app/service.py",
        patch=SIMPLE_PATCH,
    )

    deleted = [
        line
        for line in diff_map.lines
        if line.kind == "deletion"
    ]

    assert len(deleted) == 1
    assert deleted[0].old_line == 11
    assert deleted[0].new_line is None
    assert (
        deleted[0].is_commentable_new_line
        is False
    )


def test_line_outside_patch_is_not_valid_inline_location():
    assert (
        is_valid_inline_location(
            filename="app/service.py",
            line_number=50,
            patch=SIMPLE_PATCH,
        )
        is False
    )


def test_added_line_is_valid_inline_location():
    assert (
        is_valid_inline_location(
            filename="app/service.py",
            line_number=12,
            patch=SIMPLE_PATCH,
        )
        is True
    )


def test_context_line_inside_patch_is_valid():
    assert (
        is_valid_inline_location(
            filename="app/service.py",
            line_number=10,
            patch=SIMPLE_PATCH,
        )
        is True
    )


def test_missing_patch_is_not_valid():
    assert (
        is_valid_inline_location(
            filename="app/service.py",
            line_number=10,
            patch=None,
        )
        is False
    )


def test_missing_line_number_is_not_valid():
    assert (
        is_valid_inline_location(
            filename="app/service.py",
            line_number=None,
            patch=SIMPLE_PATCH,
        )
        is False
    )


def test_multiple_hunks_are_supported():
    patch = """@@ -1,2 +1,2 @@
-old one
+new one
 context
@@ -20,2 +20,3 @@
 another context
+added twenty one
 final context
"""

    diff_map = parse_patch(
        filename="app/service.py",
        patch=patch,
    )

    assert (
        diff_map.contains_new_line(1)
        is True
    )

    assert (
        diff_map.contains_new_line(21)
        is True
    )

    assert (
        diff_map.contains_new_line(10)
        is False
    )


def test_commentable_lines_returns_only_new_side_lines():
    diff_map = parse_patch(
        filename="app/service.py",
        patch=SIMPLE_PATCH,
    )

    assert (
        diff_map.commentable_lines()
        == {
            10,
            11,
            12,
            13,
        }
    )


def test_nearest_commentable_line_returns_exact_line():
    line = nearest_commentable_line(
        filename="app/service.py",
        requested_line=12,
        patch=SIMPLE_PATCH,
    )

    assert line == 12


def test_nearest_commentable_line_can_find_close_line():
    patch = """@@ -20,2 +20,2 @@
 line twenty
+line twenty one
"""

    line = nearest_commentable_line(
        filename="app/service.py",
        requested_line=22,
        patch=patch,
        max_distance=2,
    )

    assert line == 21


def test_nearest_commentable_line_returns_none_when_far():
    line = nearest_commentable_line(
        filename="app/service.py",
        requested_line=100,
        patch=SIMPLE_PATCH,
        max_distance=3,
    )

    assert line is None
