from __future__ import annotations

from app import create_app


def test_user_can_read_report_from_same_organization():
    app = create_app()

    client = app.test_client()


    response = client.get(
        "/reports/1",
        headers={
            "X-Organization-ID": "100"
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["id"] == 1
    assert payload["organization_id"] == 100