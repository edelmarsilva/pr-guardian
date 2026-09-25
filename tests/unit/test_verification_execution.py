from pathlib import Path

import pytest

from analyzers.base import AnalyzerResult, AnalyzerStatus
from analyzers.tests.pytest_runner import PytestRunner
from guardian.finding_verifier import DefaultFindingVerifier


@pytest.mark.parametrize(("source", "classification"), [
    ("def test_invariant():\n    assert 200 == 403\n", "PRODUCT_DEFECT_REPRODUCED"),
    ("def test_invariant():\n    assert 403 == 403\n", "EXPECTED_BEHAVIOR_CONFIRMED"),
    ("def test_invariant():\n    raise ValueError('broken harness')\n", "ENVIRONMENT_OR_TEST_FAILURE"),
    ("def test_invariant(missing_fixture):\n    assert False\n", "ENVIRONMENT_OR_TEST_FAILURE"),
    ("import missing_guardian_dependency\n", "ENVIRONMENT_OR_TEST_FAILURE"),
    ("def invalid syntax\n", "ENVIRONMENT_OR_TEST_FAILURE"),
    ("import pytest\n@pytest.fixture\ndef data():\n    assert False\ndef test_invariant(data):\n    assert True\n", "ENVIRONMENT_OR_TEST_FAILURE"),
    ("import pytest\n@pytest.fixture\ndef data():\n    yield 1\n    assert False\ndef test_invariant(data):\n    assert data == 1\n", "ENVIRONMENT_OR_TEST_FAILURE"),
    ("import pytest\ndef test_invariant():\n    pytest.skip('no evidence')\n", "UNKNOWN_TEST_FAILURE"),
    ("# no tests\n", "ENVIRONMENT_OR_TEST_FAILURE"),
])
def test_real_pytest_failure_classification(tmp_path, source, classification):
    target = tmp_path / "target"
    target.mkdir()
    # Regression tests live outside the target checkout.
    test_file = tmp_path / "test_invariant.py"
    test_file.write_text(source)
    execution = PytestRunner().run(target, targets=[str(test_file)])
    assert DefaultFindingVerifier()._classify_test_execution(execution) == classification
    assert execution.analyzer_result.raw_output_path.is_file()


def test_missing_report_does_not_reuse_stale_success(tmp_path, monkeypatch):
    report = tmp_path / ".pr_guardian_pytest.json"
    report.write_text('{"exitcode": 0, "summary": {"passed": 1}, "tests": []}')
    monkeypatch.setattr("analyzers.tests.pytest_runner.run_command", lambda **kwargs:
        AnalyzerResult(analyzer="pytest", status=AnalyzerStatus.SUCCESS, exit_code=0))
    execution = PytestRunner().run(tmp_path, json_report_file=report.name)
    assert not report.exists()
    assert not execution.successful
    assert execution.analyzer_result.status == AnalyzerStatus.FAILED
    assert DefaultFindingVerifier()._classify_test_execution(execution) != "EXPECTED_BEHAVIOR_CONFIRMED"


@pytest.mark.parametrize("payload", ["[]", "null", '{"exitcode": 0, "summary": {"passed": "one"}, "tests": []}'])
def test_malformed_report_is_tool_failure(tmp_path, monkeypatch, payload):
    def run(**kwargs):
        report_arg = next(arg for arg in kwargs["command"] if arg.startswith("--json-report-file="))
        Path(report_arg.split("=", 1)[1]).write_text(payload)
        return AnalyzerResult(analyzer="pytest", status=AnalyzerStatus.SUCCESS, exit_code=0)
    monkeypatch.setattr("analyzers.tests.pytest_runner.run_command", run)
    result = PytestRunner().run(tmp_path)
    assert result.analyzer_result.status == AnalyzerStatus.FAILED
    assert not result.successful


def test_default_reports_are_distinct_per_execution(tmp_path):
    test_file = tmp_path / "test_safe.py"
    test_file.write_text("def test_safe():\n    assert 1 == 1\n")
    first = PytestRunner().run(tmp_path, targets=[str(test_file)])
    second = PytestRunner().run(tmp_path, targets=[str(test_file)])
    assert first.analyzer_result.raw_output_path != second.analyzer_result.raw_output_path
    assert first.successful and second.successful
