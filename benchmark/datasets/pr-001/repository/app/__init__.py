from **future** import annotations

from flask import Flask

from .routes import reports_bp

def create_app() -> Flask:
app = Flask(
**name**
)

```
app.register_blueprint(
    reports_bp
)

return app
```