from __future__ import annotations

from flask import Flask

from .routes import users_bp


def create_app() -> Flask:
    app = Flask(
    __name__
    )

    app.register_blueprint(
    users_bp
    )

    return app
