from **future** import annotations

from flask import (
Blueprint,
flash,
redirect,
render_template,
request,
url_for,
)

from app.services.review_service import (
ReviewService,
ReviewServiceError,
)

dashboard_bp = Blueprint(
"dashboard",
**name**,
)

@dashboard_bp.get("/")
def index():
return render_template(
"index.html"
)

@dashboard_bp.post("/analyze")
def analyze():
owner = (
request.form
.get("owner", "")
.strip()
)

```
repository = (
    request.form
    .get("repository", "")
    .strip()
)

pull_number_raw = (
    request.form
    .get("pull_number", "")
    .strip()
)

validation_error = (
    _validate_analysis_request(
        owner=owner,
        repository=repository,
        pull_number_raw=pull_number_raw,
    )
)

if validation_error:
    flash(
        validation_error,
        "error",
    )

    return redirect(
        url_for(
            "dashboard.index"
        )
    )

pull_number = int(
    pull_number_raw
)

service = ReviewService()

try:
    result = service.analyze(
        owner=owner,
        repository=repository,
        pull_number=pull_number,
    )
except ReviewServiceError as exc:
    flash(
        str(exc),
        "error",
    )

    return redirect(
        url_for(
            "dashboard.index"
        )
    )

return redirect(
    url_for(
        "reviews.review_detail",
        pr_id=(
            result.pull_request.identifier
        ),
    )
)
```

def _validate_analysis_request(
*,
owner: str,
repository: str,
pull_number_raw: str,
) -> str | None:
if not owner:
return "GitHub owner is required."

```
if not repository:
    return "GitHub repository is required."

if not pull_number_raw:
    return "Pull Request number is required."

try:
    pull_number = int(
        pull_number_raw
    )
except ValueError:
    return (
        "Pull Request number must be "
        "a positive integer."
    )

if pull_number <= 0:
    return (
        "Pull Request number must be "
        "greater than zero."
    )

if "/" in owner or "/" in repository:
    return (
        "Owner and repository must be "
        "provided separately."
    )

return None
```