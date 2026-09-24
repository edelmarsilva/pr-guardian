from **future** import annotations

import os

from flask import Flask

from .routes import (
dashboard_bp,
reviews_bp,
webhooks_bp,
)

def create_app(
config: dict | None = None,
) -> Flask:
app = Flask(
**name**,
template_folder="templates",
static_folder="static",
)

```
app.config.from_mapping(
    SECRET_KEY=os.getenv(
        "FLASK_SECRET_KEY",
        "dev-only-change-me",
    ),

    GITHUB_TOKEN=os.getenv(
        "GITHUB_TOKEN"
    ),

    GITHUB_WEBHOOK_SECRET=os.getenv(
        "GITHUB_WEBHOOK_SECRET"
    ),

    PR_GUARDIAN_WORKSPACE=os.getenv(
        "PR_GUARDIAN_WORKSPACE",
        "workspace/repositories",
    ),

    PR_GUARDIAN_REPORTS=os.getenv(
        "PR_GUARDIAN_REPORTS",
        "reports",
    ),

    PR_GUARDIAN_RUN_VERIFICATION=(
        os.getenv(
            "PR_GUARDIAN_RUN_VERIFICATION",
            "true",
        ).lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
    ),
)

if config:
    app.config.update(
        config
    )

app.register_blueprint(
    dashboard_bp
)

app.register_blueprint(
    reviews_bp,
    url_prefix="/reviews",
)

app.register_blueprint(
    webhooks_bp,
    url_prefix="/webhooks",
)

return app
```