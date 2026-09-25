from __future__ import annotations

import json
import subprocess
import sys

import pytest

from analyzers.base import AnalyzerStatus
from analyzers.runner import run_command
from analyzers.static.bandit import BanditAnalyzer
from analyzers.static.pip_audit import PipAuditAnalyzer
from analyzers.static.ruff import RuffAnalyzer
from analyzers.static.semgrep import SemgrepAnalyzer


@pytest.mark.parametrize("analyzer", [RuffAnalyzer(), BanditAnalyzer(), PipAuditAnalyzer(), SemgrepAnalyzer()])
def test_optional_analyzer_absence_is_explicit(tmp_path, monkeypatch, analyzer):
    monkeypatch.setenv("PATH", "")
    result = analyzer.analyze(tmp_path)
    assert result.status == AnalyzerStatus.NOT_INSTALLED
    assert result.succeeded is False
    assert result.issues == []
    json.dumps(result.to_dict())


def test_runner_reports_execution_error(tmp_path):
    result = run_command(analyzer="controlled", command=[sys.executable, "-c", "raise SystemExit(2)"],
                         cwd=tmp_path)
    assert result.status == AnalyzerStatus.FAILED
    assert result.exit_code == 2


def test_timeout_output_is_json_serializable(tmp_path, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output=b"partial output", stderr=b"timeout detail")
    monkeypatch.setattr(subprocess, "run", timeout)
    result = run_command(analyzer="controlled", command=[sys.executable], cwd=tmp_path)
    assert result.status == AnalyzerStatus.TIMEOUT
    assert result.stdout == "partial output"
    assert result.stderr == "timeout detail"
    json.dumps(result.to_dict())
