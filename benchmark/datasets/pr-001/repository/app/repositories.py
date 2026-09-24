from **future** import annotations

from .models import REPORTS, Report

class ReportRepository:
def get_by_id(
self,
report_id: int,
) -> Report | None:
"""
Retrieve a report by its identifier.

```
    WARNING:
    This implementation intentionally represents the vulnerable
    Pull Request state used by benchmark PR-001.
    """

    for report in REPORTS:
        if report.id == report_id:
            return report

    return None
```