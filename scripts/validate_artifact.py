from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


class ArtifactValidationError(RuntimeError):
    """Raised when an artifact cannot be validated."""

def load_json(
    path: Path,
    ) -> Any:
    try:
        return json.loads(
        path.read_text(
        encoding="utf-8"
        )
        )
    except FileNotFoundError as exc:
        raise ArtifactValidationError(
        f"File does not exist: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ArtifactValidationError(
        
        f"Invalid JSON in {path}: "
        f"line {exc.lineno}, "
        f"column {exc.colno}: "
        f"{exc.msg}"
        
        ) from exc
    except OSError as exc:
        raise ArtifactValidationError(
        f"Unable to read {path}: {exc}"
        ) from exc

def format_json_path(
    path_parts,
    ) -> str:
    parts = list(
    path_parts
    )

    if not parts:
        return "$"

    result = "$"

    for part in parts:
        if isinstance(
            part,
            int,
        ):
            result += (
                f"[{part}]"
            )
        else:
            result += (
                f".{part}"
            )

    return result

def validate_artifact(
    *,
    schema_path: Path,
    artifact_path: Path,
    ) -> dict[str, Any]:
    schema = load_json(
    schema_path
    )

    artifact = load_json(
        artifact_path
    )

    try:
        validator = (
            Draft202012Validator(
                schema
            )
        )

        validator.check_schema(
            schema
        )

    except SchemaError as exc:
        raise ArtifactValidationError(
            
                f"Invalid JSON Schema "
                f"{schema_path}: {exc.message}"
            
        ) from exc

    errors = sorted(
        validator.iter_errors(
            artifact
        ),
        key=lambda error: (
            list(error.absolute_path)
        ),
    )

    formatted_errors = []

    for error in errors:
        formatted_errors.append(
            {
                "path": (
                    format_json_path(
                        error.absolute_path
                    )
                ),
                "schema_path": (
                    format_json_path(
                        error.absolute_schema_path
                    )
                ),
                "message": (
                    error.message
                ),
                "validator": (
                    error.validator
                ),
            }
        )

    return {
        "valid": not formatted_errors,
        "schema": str(
            schema_path
        ),
        "artifact": str(
            artifact_path
        ),
        "errors": (
            formatted_errors
        ),
    }

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
    description=(
    "Validate a PR Guardian JSON "
    "artifact against a JSON Schema."
    )
    )

    parser.add_argument(
        "schema",
        help=(
            "Path to JSON Schema."
        ),
    )

    parser.add_argument(
        "artifact",
        help=(
            "Path to JSON artifact."
        ),
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help=(
            "Print no output when validation succeeds."
        ),
    )

    return parser

def main() -> int:
    parser = build_parser()

    args = parser.parse_args()

    schema_path = Path(
        args.schema
    )

    artifact_path = Path(
        args.artifact
    )

    try:
        result = validate_artifact(
            schema_path=(
                schema_path
            ),
            artifact_path=(
                artifact_path
            ),
        )

    except ArtifactValidationError as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "error": str(exc),
                },
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )

        return 2

    if not result[
        "valid"
    ]:
        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )

        return 1

    if not args.quiet:
        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
