from **future** import annotations

from flask import (
Blueprint,
jsonify,
request,
)

from .database import create_connection
from .repositories import UserRepository
from .services import UserService

users_bp = Blueprint(
"users",
**name**,
)

@users_bp.get("/users")
def find_user():
email = request.args.get(
"email",
"",
)

```
connection = create_connection()

repository = UserRepository(
    connection
)

service = UserService(
    repository
)

user = service.find_user(
    email
)

if user is None:
    return (
        jsonify(
            {
                "error": "user_not_found"
            }
        ),
        404,
    )

return jsonify(
    {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
    }
)
```