from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


BENCHMARK_ROOT = (
    Path(__file__).resolve().parents[2]
    / "benchmark"
    / "datasets"
    / "pr-001"
    / "repository"
)


@pytest.fixture
def benchmark_repository() -> Path:
    if not BENCHMARK_ROOT.exists():
        pytest.fail(
            f"PR-001 benchmark repository not found: "
            f"{BENCHMARK_ROOT}"
        )

    return BENCHMARK_ROOT


@pytest.fixture
def benchmark_app(
    benchmark_repository: Path,
):
    """
    Import the synthetic benchmark application directly
    from benchmarks/datasets/pr-001/repository.
    """

    repository_path = str(
        benchmark_repository
    )

    sys.path.insert(
        0,
        repository_path,
    )

    try:
        from app import create_app

        app = create_app()

        app.config.update(
            TESTING=True,
        )

        yield app

    finally:
        sys.path.remove(
            repository_path
        )

        for module_name in list(
            sys.modules
        ):
            if (
                module_name == "app"
                or module_name.startswith(
                    "app."
                )
            ):
                del sys.modules[
                    module_name
                ]


def test_same_tenant_report_access_is_allowed(
    benchmark_app,
):
    client = benchmark_app.test_client()

    response = client.get(
        "/reports/1",
        headers={
            "X-Organization-ID": "100"
        },
    )

    assert (
        response.status_code
        == 200
    )

    payload = response.get_json()

    assert (
        payload["id"]
        == 1
    )

    assert (
        payload["organization_id"]
        == 100
    )


def test_cross_tenant_access_should_be_denied(
    benchmark_app,
):
    client = benchmark_app.test_client()

    response = client.get(
        "/reports/2",
        headers={
            "X-Organization-ID": "100"
        },
    )

    assert response.status_code in {
        403,
        404,
    }


def test_benchmark_currently_reproduces_cross_tenant_defect(
    benchmark_app,
):
    """
    This test documents the intentionally vulnerable HEAD state.

    Organization 100 requests a report owned by organization 200.
    The vulnerable PR currently returns HTTP 200.

    This is the behavior PR Guardian is expected to detect.
    """

    client = benchmark_app.test_client()

    response = client.get(
        "/reports/2",
        headers={
            "X-Organization-ID": "100"
        },
    )

    assert (
        response.status_code
        == 200
    )

    payload = response.get_json()

    assert (
        payload["organization_id"]
        == 200
    )


def test_cross_tenant_response_exposes_foreign_report_content(
    benchmark_app,
):
    client = benchmark_app.test_client()

    response = client.get(
        "/reports/2",
        headers={
            "X-Organization-ID": "100"
        },
    )

    assert (
        response.status_code
        == 200
    )

    payload = response.get_json()

    assert (
        payload["title"]
        == "Organization B Report"
    )

    assert (
        payload["content"]
        == "B confidential report"
    )


def test_missing_organization_header_is_rejected(
    benchmark_app,
):
    client = benchmark_app.test_client()

    response = client.get(
        "/reports/1"
    )

    assert (
        response.status_code
        == 401
    )


def test_invalid_organization_header_is_rejected(
    benchmark_app,
):
    client = benchmark_app.test_client()

    response = client.get(
        "/reports/1",
        headers={
            "X-Organization-ID": "invalid"
        },
    )

    assert (
        response.status_code
        == 400
    )
