from **future** import annotations

from flask import (
Blueprint,
abort,
jsonify,
request,
)

from .repositories import ReportRepository

reports_bp = Blueprint(
"reports",
**name**,
)

repository = ReportRepository()

def current_organization_id() -> int:
value = request.headers.get(
"X-Organization-ID"
)

```
if value is None:
    abort(401)

try:
    return int(value)
except ValueError:
    abort(400)
```

@reports_bp.get("/reports/[int:report_id](int:report_id)")
def get_report(
report_id: int,
):
organization_id = (
current_organization_id()
)

```
report = repository.get_by_id(
    report_id
)

if report is None:
    abort(404)

return jsonify(
    {
        "id": report.id,
        "organization_id": (
            report.organization_id
        ),
        "title": report.title,
        "content": report.content,
    }
)
```