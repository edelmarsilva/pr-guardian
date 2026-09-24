from **future** import annotations

from dataclasses import dataclass

@dataclass(slots=True)
class Report:
id: int
organization_id: int
title: str
content: str

REPORTS = [
Report(
id=1,
organization_id=100,
title="Organization A Report",
content="A confidential report",
),
Report(
id=2,
organization_id=200,
title="Organization B Report",
content="B confidential report",
),
]