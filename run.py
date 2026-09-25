from __future__ import annotations

import os

from app import create_app

app = create_app()


if __name__ == "__main__":
    host = os.getenv(
        "PR_GUARDIAN_HOST",
        "127.0.0.1",
    )

    port = int(
        os.getenv(
            "PR_GUARDIAN_PORT",
            "5000",
        )
    )

    debug = (
        os.getenv(
            "PR_GUARDIAN_DEBUG",
            "true",
        ).lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
    )

    app.run(
        host=host,
        port=port,
        debug=debug,
    )