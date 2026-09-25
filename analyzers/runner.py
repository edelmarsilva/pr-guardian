from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from .base import (
    AnalyzerResult,
    AnalyzerStatus,
)


def _as_text(output: str | bytes | None) -> str:
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output or ""


def executable_exists(
    executable: str,
) -> bool:
    return shutil.which(executable) is not None


def run_command(
    *,
    analyzer: str,
    command: list[str],
    cwd: Path,
    timeout: float = 120.0,
    env: dict[str, str] | None = None,
) -> AnalyzerResult:
    executable = command[0]

    if not executable_exists(executable):
        return AnalyzerResult(
            analyzer=analyzer,
            status=AnalyzerStatus.NOT_INSTALLED,
            command=command,
            stderr=(
                f"Executable not found: {executable}"
            ),
        )

    started = time.perf_counter()

    run_env = dict(env if env is not None else os.environ)
    for key in list(run_env.keys()):
        if key.startswith(('COV_CORE_', 'COVERAGE_')):
            del run_env[key]

    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=run_env,
        )
    except subprocess.TimeoutExpired as exc:
        duration = (
            time.perf_counter()
            - started
        )

        return AnalyzerResult(
            analyzer=analyzer,
            status=AnalyzerStatus.TIMEOUT,
            command=command,
            duration_seconds=duration,
            stdout=_as_text(exc.stdout),
            stderr=_as_text(exc.stderr),
        )
    except OSError as exc:
        duration = (
            time.perf_counter()
            - started
        )

        return AnalyzerResult(
            analyzer=analyzer,
            status=AnalyzerStatus.FAILED,
            command=command,
            duration_seconds=duration,
            stderr=str(exc),
        )

    duration = (
        time.perf_counter()
        - started
    )

    return AnalyzerResult(
        analyzer=analyzer,
        status=(
            AnalyzerStatus.SUCCESS
            if process.returncode in (0, 1)
            else AnalyzerStatus.FAILED
        ),
        command=command,
        exit_code=process.returncode,
        duration_seconds=duration,
        stdout=process.stdout,
        stderr=process.stderr,
    )
