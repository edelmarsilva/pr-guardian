from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_artifact import validate_artifact


def write_json(
    path: Path,
    payload: dict,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )


def project_root() -> Path:
    return (
        Path(__file__)
        .resolve()
        .parents[2]
    )


def finding_schema() -> Path:
    return (
        project_root()
        / "schemas"
        / "finding.schema.json"
    )


def verification_schema() -> Path:
    return (
        project_root()
        / "schemas"
        / "verification.schema.json"
    )


def valid_finding_payload() -> dict:
    return {
        "reviewer": "security-review",
        "findings": [
            {
                "id": "SEC-001",
                "category": "TENANT_ISOLATION",
                "severity": "HIGH",
                "confidence": "LIKELY",
                "title": (
                    "Report lookup is not "
                    "scoped by organization"
                ),
                "description": (
                    "The repository lookup "
                    "uses report_id without "
                    "organization_id."
                ),
                "file": (
                    "app/repositories.py"
                ),
                "line": 24,
                "evidence": [
                    (
                        "Repository query "
                        "filters only by "
                        "report_id."
                    )
                ],
                "impact": (
                    "Cross-tenant access "
                    "may be possible."
                ),
                "recommendation": (
                    "Scope the query using "
                    "the authenticated "
                    "organization."
                ),
                "verification_status": (
                    "UNVERIFIED"
                ),
                "origin": (
                    "INTRODUCED_BY_PR"
                ),
                "reviewer": (
                    "security-review"
                ),
                "metadata": {
                    "root_cause": (
                        "missing organization "
                        "scope"
                    )
                },
            }
        ],
    }


def test_valid_finding_artifact_passes_validation(
    tmp_path: Path,
):
    artifact = (
        tmp_path
        / "security-review.json"
    )

    write_json(
        artifact,
        valid_finding_payload(),
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is True
    )

    assert (
        result["errors"]
        == []
    )


def test_invalid_severity_is_rejected(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "findings"
    ][0][
        "severity"
    ] = "VERY_HIGH"

    artifact = (
        tmp_path
        / "invalid-severity.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )

    assert any(
        "severity"
        in error["path"]
        for error in result[
            "errors"
        ]
    )


def test_missing_required_finding_id_is_rejected(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    del payload[
        "findings"
    ][0]["id"]

    artifact = (
        tmp_path
        / "missing-id.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )

    assert any(
        "'id' is a required property"
        in error["message"]
        for error in result[
            "errors"
        ]
    )


def test_unknown_reviewer_is_rejected(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "reviewer"
    ] = "performance-review"

    artifact = (
        tmp_path
        / "invalid-reviewer.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )


def test_additional_top_level_property_is_rejected(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "unexpected"
    ] = "value"

    artifact = (
        tmp_path
        / "additional-property.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )

    assert any(
        error["validator"]
        == "additionalProperties"
        for error in result[
            "errors"
        ]
    )


def test_additional_finding_property_is_rejected(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "findings"
    ][0][
        "made_up_field"
    ] = True

    artifact = (
        tmp_path
        / "invalid-finding-field.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )


def test_invalid_confidence_is_rejected(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "findings"
    ][0][
        "confidence"
    ] = "CERTAIN"

    artifact = (
        tmp_path
        / "invalid-confidence.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )


def test_invalid_verification_status_is_rejected(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "findings"
    ][0][
        "verification_status"
    ] = "PROBABLY_VERIFIED"

    artifact = (
        tmp_path
        / "invalid-verification.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )


def test_invalid_origin_is_rejected(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "findings"
    ][0][
        "origin"
    ] = "UNKNOWN_SOURCE"

    artifact = (
        tmp_path
        / "invalid-origin.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )


def test_line_number_must_be_positive(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "findings"
    ][0][
        "line"
    ] = 0

    artifact = (
        tmp_path
        / "invalid-line.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )


def test_empty_evidence_list_is_allowed(
    tmp_path: Path,
):
    payload = (
        valid_finding_payload()
    )

    payload[
        "findings"
    ][0][
        "evidence"
    ] = []

    artifact = (
        tmp_path
        / "empty-evidence.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is True
    )


def test_empty_findings_list_is_valid(
    tmp_path: Path,
):
    payload = {
        "reviewer": (
            "security-review"
        ),
        "findings": [],
    }

    artifact = (
        tmp_path
        / "no-findings.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            finding_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is True
    )


def test_valid_verification_artifact_passes(
    tmp_path: Path,
):
    payload = {
        "pr_id": (
            "example-project-pr-42"
        ),
        "results": [
            {
                "finding_id": (
                    "SEC-001"
                ),
                "method": (
                    "GENERATED_REGRESSION_TEST"
                ),
                "status": (
                    "VERIFIED"
                ),
                "evidence": [
                    (
                        "Regression test "
                        "reproduced the defect."
                    )
                ],
                "command": (
                    "pytest test_sec_001.py"
                ),
                "test_file": (
                    "test_sec_001.py"
                ),
                "expected_result": (
                    "403 or 404"
                ),
                "actual_result": (
                    "200"
                ),
                "notes": (
                    "Cross-tenant access "
                    "was reproduced."
                ),
                "metadata": {
                    "failure_class": (
                        "PRODUCT_DEFECT"
                    )
                },
            }
        ],
    }

    artifact = (
        tmp_path
        / "verification.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            verification_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is True
    )


def test_unknown_verification_method_is_rejected(
    tmp_path: Path,
):
    payload = {
        "pr_id": "pr-42",
        "results": [
            {
                "finding_id": (
                    "SEC-001"
                ),
                "method": (
                    "MAGIC_AI_CHECK"
                ),
                "status": (
                    "VERIFIED"
                ),
            }
        ],
    }

    artifact = (
        tmp_path
        / "invalid-method.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            verification_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )


def test_unknown_verification_status_is_rejected(
    tmp_path: Path,
):
    payload = {
        "pr_id": "pr-42",
        "results": [
            {
                "finding_id": (
                    "SEC-001"
                ),
                "method": (
                    "DIRECT_CODE_EVIDENCE"
                ),
                "status": (
                    "CONFIRMED_MAYBE"
                ),
            }
        ],
    }

    artifact = (
        tmp_path
        / "invalid-status.json"
    )

    write_json(
        artifact,
        payload,
    )

    result = validate_artifact(
        schema_path=(
            verification_schema()
        ),
        artifact_path=artifact,
    )

    assert (
        result["valid"]
        is False
    )
