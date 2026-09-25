from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

from .base import (
    AnalyzerResult,
    AnalyzerStatus,
)


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

    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
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
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
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
        status=AnalyzerStatus.SUCCESS,
        command=command,
        exit_code=process.returncode,
        duration_seconds=duration,
        stdout=process.stdout,
        stderr=process.stderr,
    )
