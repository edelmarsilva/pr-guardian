from __future__ import annotations

from app import create_app

def test_find_existing_user():
    app = create_app()

client = app.test_client()

response = client.get(
    "/users",
    query_string={
        "email": "alice@example.com"
    },
)

assert response.status_code == 200

payload = response.get_json()

assert payload["email"] == (
    "alice@example.com"
)
